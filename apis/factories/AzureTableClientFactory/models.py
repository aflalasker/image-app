from typing import Annotated, NewType

from azure.core.credentials import AzureNamedKeyCredential
from azure.data.tables import TableEntity
from pydantic import BaseModel, Field


class AzureTableClientFactoryConfig(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    credentials: Annotated[
        AzureNamedKeyCredential,
        Field(description="The AzureNamedKeyCredential to use for authentication."),
    ]
    storage_account_table_endpoint: Annotated[
        str,
        Field(description="The URL of the Azure Storage account table endpoint."),
    ]
    table_name: Annotated[
        str, Field(description="The name of the table to connect to.")
    ]


class DeleteShortUrlTableEntityRequest(BaseModel):
    partition_key: Annotated[
        str, Field(description="The partition key of the entity to delete.")
    ]
    row_key: Annotated[str, Field(description="The row key of the entity to delete.")]


Column = NewType("Column", str)


class QueryFilter(BaseModel):
    column: Annotated[
        Column,
        Field(description="The column to filter on.", default=Column("PartitionKey")),
    ]
    operator: Annotated[
        str, Field(description="The operator to use for the filter.", default="eq")
    ]
    value: Annotated[str, Field(description="The value to filter on.")]

    def construct_filter(self) -> str:
        return (
            f"{self.column} {self.operator} '{self.value}' and RowKey eq '{self.value}'"
        )


class ShortUrlTableEntity(TableEntity):
    def __init__(self, PartitionKey: str, RowKey: str, url: str, **kwargs) -> None:
        super().__init__(PartitionKey=PartitionKey, RowKey=RowKey, url=url, **kwargs)
