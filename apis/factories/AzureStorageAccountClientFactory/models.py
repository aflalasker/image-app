from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class AzureStorageAccountClientConfig(BaseModel):
    name: Annotated[str, Field(description="The Azure Storage Account Name")]
    key: Annotated[str, Field(description="The Azure Storage Account Key")]
    url: Annotated[str, Field(description="The Azure Storage Account URL")]


RESOLUTIONS = {"720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160)}


class Resolutions(str, Enum):
    _720p = "720p"
    _1080p = "1080p"
    _4k = "4k"

    def get_dimension(self) -> tuple:
        return RESOLUTIONS[self.value]
