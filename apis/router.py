import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Annotated, List
from uuid import uuid4

from pydantic import BaseModel, computed_field

from factories.AzureTableClientFactory.client import AzureTableClientFactory
from factories.AzureTableClientFactory.models import (
    AzureTableClientFactoryConfig,
    ShortUrlTableEntity,
)
from url_shortener.models import ShortUrlCommonResponse
from auth import azure_scheme, decode_jwt_token
from fastapi import FastAPI, HTTPException, Request, Security, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi_azure_auth.user import Claims
from health.router import health_router
from photos.router import determine_storage_account_config, photos_router
from photos.models import ImageResizeResponse, PresignedUrlResponse, ImageResizeRequest
from factories.AzureStorageAccountClientFactory.client import (
    AzureStorageAccountClientFactory,
    AzureNamedKeyCredential,
    Resolutions,
)
from settings import settings
from starlette.datastructures import MutableHeaders
from telemetry import initialize_telemetry, metrics_wrapper
from url_shortener.router import generate_short_id, url_shortener_router

logger: logging.Logger = logging.getLogger(__name__)


logger.info("Creating FastAPI app instance")
app = FastAPI(
    docs_url="/docs",
    version="1.0.0",
    title="Image App API",
    summary="API for Image Sharing App",
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.OPEN_API_CLIENT_ID,
        "scopes": settings.SCOPE,
    },
    openapi_tags=[
        {"name": "Image Sharing API", "description": "API for Image Sharing App"},
        {"name": "Photos", "description": "Operations with photos"},
        {"name": "URL Shortener", "description": "Operations with URL Shortener"},
        {"name": "Health Check", "description": "Health check operations"},
        {"name": "Registered User", "description": "Operations for registered users"},
        {"name": "Guest Access", "description": "Operations for guest users"},
        {"name": "Presigned URLs", "description": "Operations for presigned URLs"},
        {"name": "Image Processing", "description": "Operations for image processing"},
    ],
)

_ALLOWED_ORIGINS = settings.ALLOWED_HOSTS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_telemetry(app=app)


@asynccontextmanager
async def lifespan(azure_scheme: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()
    yield


@app.middleware(middleware_type="http")
async def add_claims_header(request: Request, call_next):
    new_header = MutableHeaders(headers=request.headers)
    if "Authorization" in request.headers:
        claims = Claims(
            **decode_jwt_token(
                token=request.headers["Authorization"],
                jwks_url=settings.JWKS_URL,
                audience=settings.APP_CLIENT_ID,
            )
        )

        new_header["X-User-Claims"] = claims.model_dump_json(
            exclude_none=True, exclude_unset=True
        )
        new_header["X-User-Is-Guest"] = str(False)
        new_header["X-User-Oid"] = claims.oid
        metrics_wrapper.increment_user_type(user_type="Registered")
    else:
        new_header["X-User-Is-Guest"] = str(True)
        new_header["X-User-Oid"] = str(uuid4())
        metrics_wrapper.increment_user_type(user_type="Guest")

    request._headers = new_header
    request.scope.update(headers=request.headers.raw)
    response = await call_next(request)
    return response


app.include_router(
    router=url_shortener_router, tags=["Image Sharing API", "URL Shortener"]
)
app.include_router(
    router=photos_router,
    tags=["Image Sharing API", "Photos", "Registered User"],
    dependencies=[Security(dependency=azure_scheme)],
)
app.include_router(
    router=photos_router,
    tags=["Image Sharing API", "Photos", "Guest Access"],
    prefix="/guest",
)
app.include_router(
    router=health_router, tags=["Image Sharing API", "Health Check"], prefix="/health"
)


class OrchestratorResponse(BaseModel):
    image_resize_responses: List[ImageResizeResponse]
    short_url_responses: List[ShortUrlCommonResponse]

    @computed_field
    @property
    def mapped_items(self) -> List[dict]:
        return [
            {
                "image_resize_response": image_resize_response,
                "short_url_response": short_url_response,
            }
            for image_resize_response, short_url_response in zip(
                self.image_resize_responses, self.short_url_responses
            )
        ]


@app.post(path="/orchestrate", tags=["Image Sharing API", "Image Processing"])
async def orchestrate(
    request_body: Annotated[PresignedUrlResponse, Body],
    request: Request,
    background_task: BackgroundTasks,
):
    image_resize_requests: list[ImageResizeRequest] = [
        ImageResizeRequest(
            name=request_body.blob_name,
            container_name=request_body.container_id,
            folder_name=request_body.folder_name,
            resolution=resolution,
        )
        for resolution in Resolutions
    ]

    client_config = determine_storage_account_config(request.headers)
    client = AzureStorageAccountClientFactory(
        account_name=client_config.name, account_key=client_config.key
    )

    for resize_command in image_resize_requests:
        background_task.add_task(
            client.resize_image,
            container_name=resize_command.container_name,
            folder_name=resize_command.folder_name,
            blob_name=resize_command.name,
            resolution=resize_command.resolution,
        )

    file_extension: str = request_body.blob_name.split(".")[-1]

    metrics_wrapper.increment_image_type(image_type=file_extension)

    image_resize_responses: list[ImageResizeResponse] = [
        ImageResizeResponse(
            url=f"{client_config.url}/{str(resize_request.container_name)}/{str(resize_request.folder_name)}/{resize_request.resolution.value}.{file_extension}",
            resolution=resize_request.resolution.value,
        )
        for resize_request in image_resize_requests
    ]

    azure_table_client = AzureTableClientFactory(
        config=AzureTableClientFactoryConfig(
            storage_account_table_endpoint=settings.AZURE_TABLE_STORAGE_ACCOUNT_URL,
            table_name=settings.AZURE_STORAGE_ACCOUNT_TABLE_NAME,
            credentials=AzureNamedKeyCredential(
                name=settings.AZURE_TABLE_STORAGE_ACCOUNT_NAME,
                key=settings.AZURE_STORAGE_ACCOUNT_TABLE_KEY,
            ),
        )
    )

    short_url_responses: List[ShortUrlCommonResponse] = []
    for image_resize_response in image_resize_responses:
        short_id: str = generate_short_id(url=image_resize_response.url)
        entity = ShortUrlTableEntity(
            PartitionKey=short_id, RowKey=short_id, url=str(image_resize_response.url)
        )

        try:
            azure_table_client.insert_entity(entity=entity)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        short_url = f"{settings.HTTP_PROTOCOL}{settings.DNS_TO_USE}/s/{short_id}"
        response = ShortUrlCommonResponse(
            short_id=short_id,
            short_url=short_url,
            original_url=image_resize_response.url,
            should_redirect=False,
        )

        short_url_responses.append(response)

    return OrchestratorResponse(
        image_resize_responses=image_resize_responses,
        short_url_responses=short_url_responses,
        presigned_url_response=request_body,
    ).mapped_items
