import logging
from typing import Annotated
from uuid import UUID

from factories.AzureStorageAccountClientFactory.client import (
    AzureStorageAccountClientFactory,
)
from factories.AzureStorageAccountClientFactory.models import (
    AzureStorageAccountClientConfig,
)
from fastapi import APIRouter, BackgroundTasks, Body, Header, Request
from settings import settings
from telemetry import metrics_wrapper

from .models import (
    ImageResizeRequest,
    ImageResizeResponse,
    PhotoDetails,
    PresignedUrlResponse,
)

logger: logging.Logger = logging.getLogger(__name__)

_PREFIX = "photos"
_PATH_PREFIX = f"/{_PREFIX}"

photos_router = APIRouter(prefix=_PATH_PREFIX)


def is_user_guest(headers: Header) -> bool:
    if headers["X-User-Is-Guest"] == "True":
        return True
    return False


def get_user_oid(headers) -> UUID:
    oid = headers["X-User-Oid"]
    oid = UUID(oid)
    return oid


def determine_storage_account_config(
    headers,
) -> AzureStorageAccountClientConfig:
    if is_user_guest(headers):
        account_name = settings.AZURE_GUEST_STORAGE_ACCOUNT_NAME
        account_key = settings.AZURE_GUEST_STORAGE_ACCOUNT_KEY
        url = settings.AZURE_GUEST_STORAGE_ACCOUNT_URL
    else:
        account_name = settings.AZURE_REGISTERED_STORAGE_ACCOUNT_NAME
        account_key = settings.AZURE_REGISTERED_STORAGE_ACCOUNT_KEY
        url = settings.AZURE_REGISTERED_STORAGE_ACCOUNT_URL
    return AzureStorageAccountClientConfig(name=account_name, key=account_key, url=url)


@photos_router.post(
    path="/get-signed-url",
    summary="Get a signed URL for uploading a photo",
    tags=["Presigned URLs"],
)
async def get_signed_url(
    request: Request, photo_details: Annotated[PhotoDetails, Body]
) -> PresignedUrlResponse:
    logger.info("Getting signed URL for photo upload")
    client_config = determine_storage_account_config(request.headers)
    client = AzureStorageAccountClientFactory(
        account_name=client_config.name, account_key=client_config.key
    )

    container_name: UUID = get_user_oid(request.headers)

    logger.info(
        f"Generating signed URL for blob '{photo_details.name}' in container '{container_name}'"
    )

    signed_url = client.generate_post_signed_url(
        container_name=str(container_name), blob_name=photo_details.name
    )

    logger.info(f"Signed URL generated: {signed_url}")
    metrics_wrapper.increment_upload_request()

    return PresignedUrlResponse(url=signed_url)


@photos_router.post(path="/resize", summary="Resize a photo", tags=["Image Processing"])
async def resize_photo(
    resize_request: ImageResizeRequest,
    request: Request,
    background_task: BackgroundTasks,
) -> ImageResizeResponse:
    client_config = determine_storage_account_config(request.headers)
    client = AzureStorageAccountClientFactory(
        account_name=client_config.name, account_key=client_config.key
    )

    logger.info(
        f"Background Task: Resizing image for request {resize_request.model_dump()}"
    )
    background_task.add_task(
        client.resize_image,
        container_name=resize_request.container_name,
        folder_name=resize_request.folder_name,
        blob_name=resize_request.name,
        resolution=resize_request.resolution,
    )

    metrics_wrapper.increment_resolution_request(
        resolution=resize_request.resolution.value
    )

    file_extension: str = resize_request.name.split(".")[-1]

    metrics_wrapper.increment_image_type(image_type=file_extension)

    return ImageResizeResponse(
        url=f"{client_config.url}/{str(resize_request.container_name)}/{str(resize_request.folder_name)}/{resize_request.resolution.value}.{file_extension}",
        resolution=resize_request.resolution.value,
    )
