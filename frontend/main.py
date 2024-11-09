import streamlit as st
import httpx
from typing import List, Dict, Optional, Annotated
from pydantic import BaseModel, Field, HttpUrl, UUID4
from enum import Enum
from settings import settings


class PresignedURLResponse(BaseModel):
    url: Annotated[
        HttpUrl, Field(description="The presigned URL for uploading the photo")
    ]
    storage_account_url: Annotated[
        HttpUrl, Field(description="The URL of the Azure Storage account")
    ]

    container_id: Annotated[
        UUID4, Field(description="The ID of the Azure Storage container")
    ]

    folder_name: Annotated[
        UUID4, Field(description="The name of the folder in the container")
    ]

    blob_name: Annotated[
        str, Field(description="The name of the blob in the container")
    ]

    direct_url: Annotated[
        HttpUrl, Field(description="The direct URL to the uploaded photo")
    ]


class ShortUrlCommonResponse(BaseModel):
    short_id: Annotated[str, Field(description="The shortened URL.")]
    short_url: Annotated[HttpUrl | None, Field(description="The shortened URL.")] = None
    original_url: Annotated[HttpUrl, Field(description="The original URL.")]
    should_redirect: Annotated[
        bool, Field(description="Whether the URL should redirect.")
    ] = True


RESOLUTIONS = {"720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160)}


class Resolutions(str, Enum):
    _720p = "720p"
    _1080p = "1080p"
    _4k = "4k"

    def get_dimension(self) -> tuple:
        return RESOLUTIONS[self.value]


class ImageResizeResponse(BaseModel):
    url: Annotated[HttpUrl, Field(description="The URL of the resized image")]
    resolution: Annotated[
        Resolutions, Field(description="The resolution to resize the image to")
    ]


class ImageResizeAndShortUrlResponse(BaseModel):
    image_resize_response: Annotated[
        ImageResizeResponse, Field(description="The resized image response")
    ]
    short_url_response: Annotated[
        ShortUrlCommonResponse, Field(description="The shortened URL response")
    ]


# Initialize session state for caching container-folder pairs
if "container_folder_pairs" not in st.session_state:
    st.session_state.container_folder_pairs = []


class ImageHandler:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url

    def get_presigned_url(self, filename: str) -> PresignedURLResponse:
        with httpx.Client(timeout=10) as client:
            response = client.post(
                f"{self.backend_url}guest/photos/get-signed-url",
                json={"filename": filename},
            )
            if response.is_error:
                st.error("Failed to get a presigned URL. Please try again.")
                return None
            return PresignedURLResponse(**response.json())

    def upload_image(self, presigned_url: str, file_content: bytes) -> bool:
        with httpx.Client(
            timeout=10, headers={"x-ms-blob-type": "BlockBlob"}
        ) as client:
            response = client.put(presigned_url, content=file_content)
            if response.is_error:
                st.error("Failed to upload the image. Please try again.")
                return False
            return True

    def request_image_resize(self, url: str) -> Optional[List[str]]:
        with httpx.Client(timeout=10) as client:
            response = client.post(
                f"{self.backend_url}orchestrate",
                json={
                    "url": url,
                },
            )
            if response.is_error:
                st.error("Failed to resize the image. Please try again.")
                return None
            return response.json()

    async def list_folder_contents(
        self, container_name: str, folder_name: str
    ) -> Optional[List[Dict]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.backend_url}/list-folder-contents",
                params={"container_name": container_name, "folder_name": folder_name},
            )
            if response.is_error:
                st.error(f"Failed to list images for {folder_name}. Please try again.")
                return None
            return response.json().get("image_files", [])


def handle_image_upload(image_handler: ImageHandler):
    uploaded_file = st.file_uploader(
        "Upload an image", type=["png", "jpeg"], accept_multiple_files=False
    )
    if not uploaded_file:
        return

    print(uploaded_file.name)

    filename = uploaded_file.name

    presigned_data = image_handler.get_presigned_url(filename)
    if not presigned_data:
        return

    image_handler.upload_image(str(presigned_data.url), uploaded_file.getvalue())

    st.success("Image uploaded successfully!")

    image_resize_and_short_url_responses: List[ImageResizeAndShortUrlResponse] = [
        ImageResizeAndShortUrlResponse(**responses)
        for responses in image_handler.request_image_resize(url=str(presigned_data.url))
    ]

    print(image_resize_and_short_url_responses)

    st.write("Image resizing completed. Here are the resized images:")
    for response in image_resize_and_short_url_responses:
        st.write(
            f"Short URL for {response.image_resize_response.resolution.value} image."
        )
        st.code(response.short_url_response.short_url, language="html")


def main():
    image_handler = ImageHandler(backend_url=str(settings.BACKEND_API_URL))
    menu_options = ["Upload Image", "List Image Folders"]
    selected_option = st.sidebar.radio("Navigate", menu_options)

    if selected_option == "Upload Image":
        handle_image_upload(image_handler)


if __name__ == "__main__":
    main()
