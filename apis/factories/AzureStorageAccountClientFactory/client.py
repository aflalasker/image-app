import logging
from datetime import datetime, timedelta
from io import BytesIO
from uuid import uuid4

from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobClient,
    BlobSasPermissions,
    BlobServiceClient,
    ContainerClient,
    generate_blob_sas,
)
from PIL import Image
from PIL.ImageFile import ImageFile

from .models import Resolutions

logger: logging.Logger = logging.getLogger(__name__)


class AzureStorageAccountContainerDoesNotExistException(Exception):
    def __init__(self, name: str) -> None:
        self.name: str = name


class AzureStorageAccountContainerCreationFailedException(Exception):
    def __init__(self, name: str) -> None:
        self.name: str = name


class AzureStorageAccountClientFactory:
    def __init__(self, account_name: str, account_key: str) -> None:
        self.account_name: str = account_name
        self.account_key: str = account_key
        self.credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=self.credential,
        )

    def generate_post_signed_url(
        self,
        container_name: str,
        blob_name: str,
        expiry_hours: int = 1,
    ) -> str:
        if not self._container_exists(container_name=container_name):
            self._create_container(container_name=container_name)
            self._make_container_public(container_name=container_name)

        logger.info(
            f"Generating signed URL for blob '{blob_name}' in container '{container_name}'"
        )

        blob_name, ext = blob_name.split(".")
        blob_name = f"{str(uuid4())}/original.{ext}"

        sas_token: str = generate_blob_sas(
            account_name=self.account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=self.account_key,
            permission=BlobSasPermissions(write=True),
            expiry=datetime.now() + timedelta(hours=expiry_hours),
        )

        return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

    def generate_get_signed_url(
        self, container_name: str, blob_name: str, expiry_hours: int = 1
    ) -> str:
        if not self._container_exists(
            container_client=self.blob_service_client.get_container_client(
                container=container_name
            )
        ):
            raise AzureStorageAccountContainerDoesNotExistException(
                f"Container '{container_name}' does not exist."
            )

        sas_token = generate_blob_sas(
            account_name=self.account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=self.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now() + timedelta(hours=expiry_hours),
        )
        return f"https://{self.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

    def resize_image(
        self,
        container_name: str,
        folder_name: str,
        blob_name: str,
        resolution: Resolutions,
    ) -> None:
        logger.info("Resizing photo: %s", resolution.value)

        # Resized image properties
        original_blob_extension: str = blob_name.split(".")[-1]
        resized_blob_name: str = f"{resolution.value}.{original_blob_extension}"
        resized_blob_path: str = f"{folder_name}/{resized_blob_name}"

        # Original image properties
        original_image_path: str = f"{folder_name}/{blob_name}"

        original_blob_client: BlobClient = self.blob_service_client.get_blob_client(
            container=container_name, blob=original_image_path
        )
        original_blob: bytes = original_blob_client.download_blob().readall()
        image: ImageFile = Image.open(BytesIO(original_blob))

        resized_image: Image.Image = image.resize(size=resolution.get_dimension())

        output = BytesIO()
        resized_image.save(output, format=original_blob_extension)
        output.seek(0)

        resized_blob_client: BlobClient = self.blob_service_client.get_blob_client(
            container=container_name, blob=resized_blob_path
        )
        resized_blob_client.upload_blob(data=output, overwrite=True)

        logger.info(f"Image processing complete for blob: {original_image_path}")

    def delete_container(self, container_name: str) -> None:
        logger.info(f"Deleting container '{container_name}'")
        container_client: ContainerClient = (
            self.blob_service_client.get_container_client(container=container_name)
        )
        try:
            container_client.delete_container()
            logger.info(f"Container '{container_name}' deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete container '{container_name}': {e}")

    def _create_container(self, container_name: str) -> None:
        logger.info(f"Creating container '{container_name}'")
        container_client: ContainerClient = (
            self.blob_service_client.get_container_client(container=container_name)
        )
        if not self._container_exists(container_name=container_client):
            try:
                container_client.create_container()
                logger.info(f"Container '{container_name}' created successfully.")
            except AzureStorageAccountContainerCreationFailedException as e:
                logger.error(f"Failed to create container '{container_name}': {e}")

    def _make_container_public(self, container_name: str) -> None:
        logger.info(f"Making container '{container_name}' public.")
        self.blob_service_client.get_container_client(
            container=container_name
        ).set_container_access_policy(public_access="container", signed_identifiers={})

    def _container_exists(self, container_name: str) -> bool:
        try:
            self.blob_service_client.get_container_client(
                container=container_name
            ).get_container_properties()
            logger.info(f"Container '{container_name}' exists.")
            return True
        except Exception:
            logger.info(f"Container '{container_name}' does not exist.")
            return False
