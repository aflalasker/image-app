from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl


class ShortUrlCommonResponse(BaseModel):
    short_id: Annotated[str, Field(description="The shortened URL.")]
    short_url: Annotated[HttpUrl | None, Field(description="The shortened URL.")] = None
    original_url: Annotated[HttpUrl, Field(description="The original URL.")]
    should_redirect: Annotated[
        bool, Field(description="Whether the URL should redirect.")
    ] = True
