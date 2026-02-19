import os
import logging
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timezone

import httpx
from azure.identity import DefaultAzureCredential, ClientSecretCredential, ManagedIdentityCredential
from httpx import Auth
from pydantic import SecretStr

logger = logging.getLogger(__name__)


class AzureAuthProvider(Auth):
    """
    Agent auth provider that uses Azure credentials for authentication.

    Supports multiple credential types:
    1. Service Principal (Environment Variables): CLIENT_ID, CLIENT_SECRET, TENANT_ID
    2. Managed Identity: If running in Azure with CLIENT_ID configured
    3. DefaultAzureCredential: Fallback for development (Azure CLI, etc.)

    Environment Variables:
    - CLIENT_ID: Azure Service Principal Client ID
    - CLIENT_SECRET: Azure Service Principal Client Secret
    - TENANT_ID: Azure Tenant ID
    - AZURE_SCOPE: Optional scope for token (defaults to https://management.azure.com/.default)
    """

    token: SecretStr | None = None
    expiry: datetime | None = None

    def __init__(self):
        self.credential = None
        self.token = self.get_az_cli_token()

    def get_az_cli_token(self) -> SecretStr:
        if not self.credential:
            # Check if service principal credentials are provided (production)
            if all(os.getenv(var) for var in ["CLIENT_ID", "CLIENT_SECRET", "TENANT_ID"]):
                logger.info("Using ClientSecretCredential with environment variables")
                self.credential = ClientSecretCredential(
                    tenant_id=os.getenv("TENANT_ID"),
                    client_id=os.getenv("CLIENT_ID"),
                    client_secret=os.getenv("CLIENT_SECRET")
                )
            # Check if we should use Managed Identity (Azure hosted environments)
            elif os.getenv("CLIENT_ID") and not os.getenv("CLIENT_SECRET"):
                logger.info("Using ManagedIdentityCredential with CLIENT_ID")
                self.credential = ManagedIdentityCredential(
                    client_id=os.getenv("CLIENT_ID")
                )
            else:
                # Fallback to DefaultAzureCredential with excluded credentials
                # Exclude WorkloadIdentityCredential and VisualStudioCodeCredential to reduce noise
                logger.info("Using DefaultAzureCredential (development mode)")
                self.credential = DefaultAzureCredential(
                    exclude_workload_identity_credential=True,
                    exclude_visual_studio_code_credential=True,
                    exclude_shared_token_cache_credential=True,
                    exclude_powershell_credential=True
                )

        if self.token and self.expiry and datetime.now(UTC) < self.expiry:
            return self.token

        # Get scope from environment or use default
        # Default scope for Azure Management API - adjust based on your needs
        scope = os.getenv("AZURE_SCOPE", "https://management.azure.com/.default")

        # Validate and fix scope format if needed
        if scope == "/.default":
            logger.warning("Invalid scope format '/.default' detected, using default: https://management.azure.com/.default")
            scope = "https://management.azure.com/.default"
        elif not scope.startswith("http"):
            logger.warning(f"Scope '{scope}' doesn't start with http, using default: https://management.azure.com/.default")
            scope = "https://management.azure.com/.default"

        logger.info(f"Using scope: {scope}")

        try:
            token = self.credential.get_token(scope)

            # Subtract 60 seconds to account for clock skew
            self.expiry = datetime.fromtimestamp(token.expires_on - 60, UTC)
            logger.info("Successfully obtained Azure token")
            return SecretStr(token.token)
        except Exception as e:
            logger.error(f"Failed to get Azure token: {e}")
            logger.error(f"Scope used: {scope}")
            logger.error(f"Environment check - CLIENT_ID: {'SET' if os.getenv('CLIENT_ID') else 'NOT SET'}")
            logger.error(f"Environment check - CLIENT_SECRET: {'SET' if os.getenv('CLIENT_SECRET') else 'NOT SET'}")
            logger.error(f"Environment check - TENANT_ID: {'SET' if os.getenv('TENANT_ID') else 'NOT SET'}")
            logger.error(f"Environment check - AZURE_SCOPE: {os.getenv('AZURE_SCOPE', 'NOT SET (using default)')}")
            raise

    def auth_flow(self, request: httpx.Request) -> Iterator[httpx.Request]:
        """
        Synchronous auth flow for httpx clients.
        """
        token = self.get_az_cli_token().get_secret_value()
        request.headers["Authorization"] = f"Bearer {token}"
        yield request

    async def async_auth_flow(self, request: httpx.Request) -> AsyncIterator[httpx.Request]:
        """
        Async auth flow for httpx AsyncClient.
        """
        token = self.get_az_cli_token().get_secret_value()
        request.headers["Authorization"] = f"Bearer {token}"
        yield request
