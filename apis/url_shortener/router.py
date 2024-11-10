import base64
import hashlib
import logging
import time
import urllib.parse

from fastapi.responses import RedirectResponse

from factories.AzureTableClientFactory.client import (
    AzureTableClientFactory,
)
from factories.AzureTableClientFactory.models import (
    AzureNamedKeyCredential,
    AzureTableClientFactoryConfig,
    QueryFilter,
    ShortUrlTableEntity,
)
from fastapi import APIRouter, HTTPException, Request
from settings import settings
from telemetry import metrics_wrapper

from .models import ShortUrlCommonResponse

logger: logging.Logger = logging.getLogger(__name__)

_PREFIX = "s"
_PATH_PREFIX = f"/{_PREFIX}"

url_shortener_router = APIRouter(prefix=_PATH_PREFIX)


def generate_short_id(url: str) -> str:
    current_time = str(time.time())
    combined = str(url) + current_time
    hash_object = hashlib.sha256(combined.encode())
    short_id = base64.urlsafe_b64encode(hash_object.digest()[:6]).decode("utf-8")
    short_id = short_id.rstrip("=")
    short_id = urllib.parse.quote(short_id, safe="")
    return short_id.upper()


@url_shortener_router.post(path="", summary="Create a new short URL")
async def create_url(url: str, request: Request) -> ShortUrlCommonResponse:
    logger.info(f"Creating short url for: {url}.")
    metrics_wrapper.increment_url_shortener_request(request_type="create")
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

    short_id: str = generate_short_id(url=url)
    entity = ShortUrlTableEntity(PartitionKey=short_id, RowKey=short_id, url=url)

    try:
        azure_table_client.insert_entity(entity=entity)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    short_url = f"{settings.HTTP_PROTOCOL}{settings.DNS_TO_USE}/{_PREFIX}/{short_id}"
    response = ShortUrlCommonResponse(
        short_id=short_id, short_url=short_url, original_url=url, should_redirect=False
    )

    logger.info(f"Created short url: {short_url}")

    return response


@url_shortener_router.get(
    path="/{short_id}",
    summary="Get a URL",
    response_model_exclude_none=True,
)
async def get_url(short_id: str, request: Request) -> RedirectResponse:
    logger.info(f"Getting URL for short id: {short_id}.")
    metrics_wrapper.increment_url_shortener_request(request_type="get")
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

    query_filter = QueryFilter(value=short_id)
    short_url_table_entity: ShortUrlTableEntity = azure_table_client.query_entities(
        query_filter=query_filter
    )

    if not short_url_table_entity:
        raise HTTPException(status_code=404, detail="URL not found.")

    short_url = f"{settings.HTTP_PROTOCOL}{settings.DNS_TO_USE}/{_PREFIX}/{short_id}"

    response = ShortUrlCommonResponse(
        short_id=short_id,
        short_url=short_url,
        original_url=short_url_table_entity["url"],
    )
    logger.warning(request.headers)
    logger.info(f"Resolved URL for short id: {short_id}. URL: {response.original_url}.")

    metrics_wrapper.increment_most_common_short_urls(
        short_id=short_id, original_url=response.original_url
    )

    return RedirectResponse(url=str(response.original_url))
