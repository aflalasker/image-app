from typing import Annotated

from factories.AzureStorageAccountClientFactory.models import Resolutions
from pydantic import UUID4, BaseModel, Field, HttpUrl, computed_field


class PhotoDetails(BaseModel):
    name: Annotated[
        str, Field(description="The name of the photo", default="original.png")
    ]

    @computed_field
    @property
    def is_valid_extension(self) -> bool:
        valid_extensions = (".jpeg", ".png")
        return self.name.lower().endswith(valid_extensions)

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._validate_extension

    @computed_field
    @property
    def _validate_extension(self) -> None:
        if not self.is_valid_extension:
            raise ValueError(
                f"Invalid file extension for {self.name}. Allowed extensions are: .jpeg, .png"
            )


class PresignedUrlResponse(BaseModel):
    url: Annotated[
        HttpUrl, Field(description="The presigned URL for uploading the photo")
    ]

    @computed_field
    @property
    def storage_account_url(self) -> HttpUrl:
        return "/".join(str(self.url).split("/")[:3])

    @computed_field
    @property
    def container_id(self) -> UUID4:
        return str(self.url).split("/")[3]

    @computed_field
    @property
    def folder_name(self) -> UUID4:
        return str(self.url).split("/")[4]

    @computed_field
    @property
    def blob_name(self) -> str:
        return str(self.url).split("/")[5].split("?")[0]

    @computed_field
    @property
    def direct_url(self) -> HttpUrl:
        return f"{self.storage_account_url}/{self.container_id}/{self.folder_name}/{self.blob_name}"


class ImageResizeRequest(PhotoDetails):
    container_name: Annotated[str, Field(description="The container ID")]
    folder_name: Annotated[str, Field(description="The folder name")]
    resolution: Annotated[
        Resolutions, Field(description="The resolution to resize the image to")
    ]


class ImageResizeResponse(BaseModel):
    url: Annotated[HttpUrl, Field(description="The URL of the resized image")]
    resolution: Annotated[
        Resolutions, Field(description="The resolution to resize the image to")
    ]
