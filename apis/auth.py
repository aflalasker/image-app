import jwt
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from jwt import PyJWKClient
from settings import settings
import logging

logger: logging.Logger = logging.getLogger(__name__)

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes={
        settings.SCOPE: settings.SCOPE_NAME,
    },
    allow_guest_users=True,
)


def decode_jwt_token(token: str, jwks_url: str, audience: str) -> dict:
    logger.info("Decoding JWT token")
    token = token.split(" ")[1]

    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token).key

    decoded_token = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience=audience,
    )

    logger.info("Decoded JWT token")
    return decoded_token
