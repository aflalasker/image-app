from uuid import uuid4

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from .readiness import (
    DeleteShortUrlTableEntityRequest,
    ShortUrlTableEntity,
    orchestrate_storage_account_checks,
    orchestrate_table_storage_checks,
)

health_router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: int


@health_router.get(
    path="/liveness",
    summary="Liveness probe",
    description="Check if the service is running",
)
async def liveness() -> HealthCheckResponse:
    return HealthCheckResponse(status=status.HTTP_200_OK)


_READINESS_DESCRIPTION = """

This endpoint checks if the service is ready to accept requests. It does so by checking if it is possible to interact with the storage accounts.

1. It checks if it is possible to interact with the storage account by checking if it is possible,
    1. to generate a presigned URL for a blob
    2. to upload a file to storage account using the presigned URL
    3. to read the contents of the blob using the direct URL of the blob
    4. ensured the contents of the blob are the same as the uploaded file
    5. to delete the container
2. It checks if it is possible to interact with the storage account table by 
    1. inserting an entity to the table
    2. querying for the inserted entity
    3. deleting an entity.

If all checks pass, the service is considered ready and returns a 200 status code. Otherwise, it returns a 503 status code.

"""


@health_router.get(
    path="/readiness",
    summary="Readiness probe",
    description=_READINESS_DESCRIPTION,
)
async def readiness(response: Response) -> HealthCheckResponse:
    is_possible_to_interact_with_storage_accounts: bool = (
        await orchestrate_storage_account_checks(
            container_name="success", blob_name="original.json"
        )
    )

    common_uuid = str(uuid4())

    entity_to_insert = ShortUrlTableEntity(
        PartitionKey=common_uuid, RowKey=common_uuid, url="https://test.test"
    )

    delete_to_entity = DeleteShortUrlTableEntityRequest(
        partition_key=common_uuid, row_key=common_uuid
    )

    is_possible_to_interact_with_storage_account_table: bool = (
        await orchestrate_table_storage_checks(
            insert_entity=entity_to_insert, delete_entity=delete_to_entity
        )
    )

    if all(
        [
            is_possible_to_interact_with_storage_accounts,
            is_possible_to_interact_with_storage_account_table,
        ]
    ):
        response.status_code = status.HTTP_200_OK
        return HealthCheckResponse(status=status.HTTP_200_OK)
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthCheckResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)
