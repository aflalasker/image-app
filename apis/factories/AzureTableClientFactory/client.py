import logging
from typing import List

from azure.data.tables import TableClient, TableServiceClient

from .models import (
    AzureTableClientFactoryConfig,
    DeleteShortUrlTableEntityRequest,
    QueryFilter,
    ShortUrlTableEntity,
)

logger: logging.Logger = logging.getLogger(__name__)


class AzureTableClientFactory:
    def __init__(self, config: AzureTableClientFactoryConfig) -> None:
        self.config = config
        self.client: TableClient = self._create_client()

    def _create_client(self) -> TableClient:
        table_service: TableServiceClient = TableServiceClient(
            endpoint=self.config.storage_account_table_endpoint,
            credential=self.config.credentials,
        )
        return table_service.get_table_client(table_name=self.config.table_name)

    def insert_entity(self, entity: ShortUrlTableEntity) -> None:
        try:
            logger.info(f"Inserting entity: {entity.__str__()}")
            self.client.create_entity(entity=entity)
        except Exception as e:
            logger.error(f"Error inserting entity: {e}")

    def query_entities(self, query_filter: QueryFilter) -> ShortUrlTableEntity | None:
        try:
            logger.info(
                f"Querying entities with filter: {query_filter.construct_filter()}"
            )
            entities: List[ShortUrlTableEntity] = self.client.query_entities(
                query_filter=query_filter.construct_filter()
            )

        except Exception as e:
            logger.error(f"Error querying entities: {e}")

        short_url_table_entity = next(entities, None)

        if short_url_table_entity:
            return ShortUrlTableEntity(**short_url_table_entity)

        return None

    def delete_entity(self, entity: DeleteShortUrlTableEntityRequest) -> None:
        try:
            logger.info(f"Deleting entity: {entity.model_dump()}")
            self.client.delete_entity(
                partition_key=entity.partition_key, row_key=entity.row_key
            )
        except Exception as e:
            logger.error(f"Error deleting entity: {e}")
