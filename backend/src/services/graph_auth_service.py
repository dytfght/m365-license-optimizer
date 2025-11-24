"""
Microsoft Graph Authentication Service
Handles token acquisition via MSAL (Microsoft Authentication Library)
with Redis caching and client credentials flow.
"""
from typing import Optional

import msal
import structlog
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.tenant import TenantAppRegistration
from .encryption_service import EncryptionService

logger = structlog.get_logger(__name__)


class GraphAuthService:
    """
    Service for acquiring Microsoft Graph access tokens.
    Uses MSAL client credentials flow with Redis caching.
    """

    def __init__(
        self, db: AsyncSession, redis: Redis, encryption_service: EncryptionService
    ):
        """
        Initialize Graph auth service.

        Args:
            db: Async database session
            redis: Redis client for token caching
            encryption_service: Service for decrypting client secrets
        """
        self.db = db
        self.redis = redis
        self.encryption = encryption_service
        self.base_url = settings.GRAPH_API_BASE_URL
        self.authority_base = settings.GRAPH_API_AUTHORITY

    async def get_access_token(self, tenant_id: str) -> str:
        """
        Get access token for Microsoft Graph API.
        Checks Redis cache first, then acquires new token if needed.

        Args:
            tenant_id: Azure AD tenant ID

        Returns:
            Access token string

        Raises:
            ValueError: If credentials not found or invalid
            RuntimeError: If token acquisition fails
        """
        # Check Redis cache first
        cache_key = f"graph_token:{tenant_id}"
        cached_token = await self.redis.get(cache_key)

        if cached_token:
            logger.debug("graph_token_cache_hit", tenant_id=tenant_id)
            return cached_token.decode()  # type: ignore[no-any-return]

        logger.debug("graph_token_cache_miss", tenant_id=tenant_id)

        # Get app registration from database
        app_reg = await self._get_app_registration(tenant_id)
        if not app_reg:
            raise ValueError(f"No app registration found for tenant {tenant_id}")

        # Acquire new token via MSAL
        token_response = await self._acquire_token_from_msal(app_reg)

        access_token = token_response.get("access_token")
        expires_in = token_response.get("expires_in", 3600)

        if not access_token:
            raise RuntimeError("Failed to acquire access token from MSAL")

        # Cache token in Redis with TTL (expires_in - 5min buffer)
        cache_ttl = max(expires_in - 300, 60)  # At least 1 minute
        await self.redis.set(cache_key, access_token, ex=cache_ttl)

        logger.info(
            "graph_token_acquired",
            tenant_id=tenant_id,
            expires_in=expires_in,
            cache_ttl=cache_ttl,
        )

        return access_token  # type: ignore[no-any-return]

    async def _get_app_registration(
        self, tenant_id: str
    ) -> Optional[TenantAppRegistration]:
        """
        Get app registration from database for a tenant.

        Args:
            tenant_id: Azure AD tenant ID

        Returns:
            TenantAppRegistration or None if not found
        """
        stmt = (
            select(TenantAppRegistration)
            .join(TenantAppRegistration.tenant)
            .where(TenantAppRegistration.tenant.has(tenant_id=tenant_id))
        )

        result = await self.db.execute(stmt)
        app_reg = result.scalar_one_or_none()

        if not app_reg:
            logger.warning("app_registration_not_found", tenant_id=tenant_id)

        return app_reg

    async def _acquire_token_from_msal(
        self, app_registration: TenantAppRegistration
    ) -> dict:
        """
        Acquire token from Microsoft via MSAL library.

        Args:
            app_registration: Tenant app registration with credentials

        Returns:
            Token response dict with access_token and expires_in

        Raises:
            RuntimeError: If token acquisition fails
        """
        # Decrypt client secret
        if not app_registration.client_secret_encrypted:
            raise ValueError(
                f"No client secret found for app {app_registration.client_id}"
            )

        try:
            client_secret = self.encryption.decrypt(
                app_registration.client_secret_encrypted
            )
        except Exception as e:
            logger.error(
                "client_secret_decryption_failed",
                client_id=app_registration.client_id,
                error=str(e),
            )
            raise ValueError(f"Failed to decrypt client secret: {e}") from e

        # Build authority URL
        # Extract tenant ID from authority_url (format: https://login.microsoftonline.com/{tenant_id})
        authority_parts = app_registration.authority_url.rstrip("/").split("/")
        authority_tenant_id = authority_parts[-1]
        authority = f"{self.authority_base}/{authority_tenant_id}"

        logger.debug(
            "acquiring_msal_token",
            client_id=app_registration.client_id,
            authority=authority,
        )

        # Create MSAL confidential client application
        msal_app = msal.ConfidentialClientApplication(
            client_id=app_registration.client_id,
            client_credential=client_secret,
            authority=authority,
        )

        # Acquire token for Microsoft Graph
        scopes = ["https://graph.microsoft.com/.default"]

        try:
            token_response = msal_app.acquire_token_for_client(scopes=scopes)
        except Exception as e:
            logger.error(
                "msal_token_acquisition_failed",
                client_id=app_registration.client_id,
                error=str(e),
            )
            raise RuntimeError(f"MSAL token acquisition failed: {e}") from e

        # Check for errors in response
        if "error" in token_response:
            error_desc = token_response.get("error_description", "Unknown error")
            logger.error(
                "msal_token_error",
                client_id=app_registration.client_id,
                error=token_response["error"],
                description=error_desc,
            )
            raise RuntimeError(f"MSAL error: {token_response['error']} - {error_desc}")

        logger.info(
            "msal_token_acquired_successfully",
            client_id=app_registration.client_id,
            expires_in=token_response.get("expires_in"),
        )

        return token_response  # type: ignore[no-any-return]

    async def validate_credentials(self, tenant_id: str) -> bool:
        """
        Validate that credentials work by attempting to acquire a token.

        Args:
            tenant_id: Azure AD tenant ID

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            token = await self.get_access_token(tenant_id)
            return bool(token)
        except Exception as e:
            logger.warning(
                "credential_validation_failed", tenant_id=tenant_id, error=str(e)
            )
            return False

    async def invalidate_cache(self, tenant_id: str) -> None:
        """
        Invalidate cached token for a tenant.
        Useful when credentials are updated.

        Args:
            tenant_id: Azure AD tenant ID
        """
        cache_key = f"graph_token:{tenant_id}"
        await self.redis.delete(cache_key)
        logger.info("graph_token_cache_invalidated", tenant_id=tenant_id)
