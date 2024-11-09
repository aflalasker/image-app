import logging
from typing import Annotated, Dict, List

from factories.AzureStorageAccountClientFactory.client import (
    AzureStorageAccountClientFactory,
)
from factories.AzureStorageAccountClientFactory.models import (
    AzureStorageAccountClientConfig,
)
from factories.AzureTableClientFactory.client import AzureTableClientFactory
from factories.AzureTableClientFactory.models import (
    AzureNamedKeyCredential,
    AzureTableClientFactoryConfig,
    DeleteShortUrlTableEntityRequest,
    QueryFilter,
    ShortUrlTableEntity,
)
from httpx import AsyncClient, Response
from photos.models import PresignedUrlResponse
from pydantic import BaseModel, Field, HttpUrl
from settings import settings

logger: logging.Logger = logging.getLogger(__name__)


class PresignedUrls(BaseModel):
    container_name: Annotated[str, Field(description="The name of the container")]
    blob_name: Annotated[str, Field(description="The name of the blob")]
    url: Annotated[str, Field(description="The presigned URL")]


class SuccessFileContent(BaseModel):
    success: bool = True


registered_users_storage_account = AzureStorageAccountClientConfig(
    name=settings.AZURE_REGISTERED_STORAGE_ACCOUNT_NAME,
    key=settings.AZURE_REGISTERED_STORAGE_ACCOUNT_KEY,
    url=settings.AZURE_REGISTERED_STORAGE_ACCOUNT_URL,
)

guest_users_storage_account = AzureStorageAccountClientConfig(
    name=settings.AZURE_GUEST_STORAGE_ACCOUNT_NAME,
    key=settings.AZURE_GUEST_STORAGE_ACCOUNT_KEY,
    url=settings.AZURE_GUEST_STORAGE_ACCOUNT_URL,
)

registered_users_storage_account_client = AzureStorageAccountClientFactory(
    account_name=registered_users_storage_account.name,
    account_key=registered_users_storage_account.key,
)

guest_users_storage_account_client = AzureStorageAccountClientFactory(
    account_name=guest_users_storage_account.name,
    account_key=guest_users_storage_account.key,
)

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


async def check_is_possible_to_generate_presigned_url(
    container_name: str,
    blob_name: str,
    expiry_hours: int = 1,
) -> List[PresignedUrls]:
    guest_users_url = guest_users_storage_account_client.generate_post_signed_url(
        container_name=container_name,
        blob_name=blob_name,
        expiry_hours=expiry_hours,
    )

    logger.info(f"Guest users URL: {guest_users_url}")

    registered_users_url = (
        registered_users_storage_account_client.generate_post_signed_url(
            container_name=container_name,
            blob_name=blob_name,
            expiry_hours=expiry_hours,
        )
    )

    logger.info(f"Registered users URL: {registered_users_url}")

    presigned_urls: List[PresignedUrls] = [
        PresignedUrls(
            container_name=container_name, blob_name=blob_name, url=guest_users_url
        ),
        PresignedUrls(
            container_name=container_name, blob_name=blob_name, url=registered_users_url
        ),
    ]

    return presigned_urls


async def check_if_possible_to_write_to_storage_account_using_presigned_url(
    presigned_url: PresignedUrlResponse,
) -> bool:
    headers: Dict[str, str] = {
        "x-ms-blob-type": "BlockBlob",
        "Content-Type": "application/json",
    }

    logger.info(
        f"Attempting to write to storage account using URL: {presigned_url.url}"
    )
    async with AsyncClient(headers=headers) as client:
        response: Response = await client.put(
            url=str(presigned_url.url), data=SuccessFileContent().model_dump_json()
        )

        if response.status_code == 201:
            return True

    return False


async def check_if_possible_to_read_blob_contents_from_storage_account(
    url: HttpUrl,
) -> bool:
    async with AsyncClient() as client:
        logger.info(f"Attempting to read from storage account using URL: {url}")
        response: Response = await client.get(url=url)

        if response.status_code == 200:
            data: bytes = response.content
            is_data_valid: SuccessFileContent = SuccessFileContent.model_validate_json(
                json_data=data
            )
            logger.warning(f"Data is valid: {is_data_valid}")
            return is_data_valid

    return False


async def check_if_possible_to_insert_to_storage_account_table(
    entity: ShortUrlTableEntity,
) -> bool:
    try:
        azure_table_client.insert_entity(entity=entity)
    except Exception:
        return False
    return True


async def check_if_possible_to_query_from_storage_account_table(value: str) -> bool:
    query_filter = QueryFilter(value=value)
    short_url_table_entity: ShortUrlTableEntity = azure_table_client.query_entities(
        query_filter=query_filter
    )

    if not short_url_table_entity:
        return False

    return True


async def check_if_possible_to_delete_from_storage_account_table(
    entity: DeleteShortUrlTableEntityRequest,
) -> bool:
    try:
        azure_table_client.delete_entity(entity=entity)
    except Exception:
        return False
    return True


async def orchestrate_storage_account_checks(
    container_name: str,
    blob_name: str,
) -> bool:
    presigned_urls: List[
        PresignedUrls
    ] = await check_is_possible_to_generate_presigned_url(
        container_name=container_name, blob_name=blob_name
    )

    for presigned_url in presigned_urls:
        presigned_url_response = PresignedUrlResponse(url=presigned_url.url)
        is_possible_to_write = (
            await check_if_possible_to_write_to_storage_account_using_presigned_url(
                presigned_url=presigned_url_response
            )
        )

        if not is_possible_to_write:
            logger.error(
                f"Failed to write to storage account using presigned URL: {presigned_url_response.direct_url}"
            )
            return False

        is_possible_to_read = (
            await check_if_possible_to_read_blob_contents_from_storage_account(
                url=presigned_url_response.direct_url
            )
        )

        if not is_possible_to_read:
            logger.error(
                f"Failed to read from storage account using presigned URL: {presigned_url_response.direct_url}"
            )
            return False

    if all([is_possible_to_write, is_possible_to_read]):
        registered_users_storage_account_client.delete_container(
            container_name=container_name
        )
        guest_users_storage_account_client.delete_container(
            container_name=container_name
        )

    return True


async def orchestrate_table_storage_checks(
    insert_entity: ShortUrlTableEntity,
    delete_entity: DeleteShortUrlTableEntityRequest,
) -> bool:
    is_possible_to_insert = await check_if_possible_to_insert_to_storage_account_table(
        entity=insert_entity
    )

    if not is_possible_to_insert:
        logger.error("Failed to insert entity into table storage.")
        return False

    is_possible_to_query = await check_if_possible_to_query_from_storage_account_table(
        value=delete_entity.partition_key
    )

    if not is_possible_to_query:
        logger.error("Failed to query entity from table storage.")
        return False

    is_possible_to_delete = (
        await check_if_possible_to_delete_from_storage_account_table(
            entity=delete_entity
        )
    )

    if not is_possible_to_delete:
        logger.error("Failed to delete entity from table storage.")
        return False

    return True
