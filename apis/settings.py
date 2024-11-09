from typing import List

from pydantic import HttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Azure Table Storage settings
    AZURE_TABLE_STORAGE_ACCOUNT_NAME: str

    @computed_field
    @property
    def AZURE_TABLE_STORAGE_ACCOUNT_URL(self) -> HttpUrl:
        return f"https://{self.AZURE_TABLE_STORAGE_ACCOUNT_NAME}.table.core.windows.net"

    AZURE_STORAGE_ACCOUNT_TABLE_NAME: str
    AZURE_STORAGE_ACCOUNT_TABLE_KEY: str

    # Azure Storage Account settings (Guest)
    AZURE_GUEST_STORAGE_ACCOUNT_NAME: str

    @computed_field
    @property
    def AZURE_GUEST_STORAGE_ACCOUNT_URL(self) -> HttpUrl:
        return f"https://{self.AZURE_GUEST_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"

    AZURE_GUEST_STORAGE_ACCOUNT_KEY: str

    # Azure Storage Account settings (Registered)
    AZURE_REGISTERED_STORAGE_ACCOUNT_NAME: str

    @computed_field
    @property
    def AZURE_REGISTERED_STORAGE_ACCOUNT_URL(self) -> HttpUrl:
        return f"https://{self.AZURE_REGISTERED_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"

    AZURE_REGISTERED_STORAGE_ACCOUNT_KEY: str

    # # Azure AD settings
    TENANT_ID: str
    APP_CLIENT_ID: str
    OPEN_API_CLIENT_ID: str
    REDIRECT_URIS: str = ""
    SCOPE: str
    JWKS_URL: str = "https://login.microsoftonline.com/common/discovery/keys"

    @computed_field
    @property
    def OAUTH2_REDIRECT_URIS(self) -> List[str]:
        return self.REDIRECT_URIS.split(",")

    @computed_field
    @property
    def SCOPE_NAME(self) -> str:
        return self.SCOPE.split("/")[-1]

    OTEL_EXPORTER_OTLP_ENDPOINT: str

    CONTAINER_APP_HOSTNAME: str
    ALLOWED_HOST: str

    @computed_field
    @property
    def HTTP_PROTOCOL(self) -> str:
        if self.CONTAINER_APP_HOSTNAME.startswith(
            "localhost"
        ) and self.ALLOWED_HOST.startswith("localhost"):
            return "http://"
        return "https://"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
