"""
Partner Center Authentication Service
Handles token acquisition via MSAL for Partner Center API
"""

import structlog
from msal import ConfidentialClientApplication
from redis.asyncio import Redis

from ..core.config import settings

logger = structlog.get_logger(__name__)


class PartnerCenterAuthError(Exception):
    """Exception raised for Partner Center authentication errors"""

    pass


class PartnerAuthService:
    """
    Manages Partner Center API authentication with Redis caching

    Uses MSAL (Microsoft Authentication Library) to acquire tokens
    for Partner Center API access using client credentials flow.

    Tokens are cached in Redis with TTL based on expiry time.
    """

    SCOPES = ["https://api.partnercenter.microsoft.com/.default"]
    CACHE_KEY_PREFIX = "partner_token:"

    def __init__(self, redis: Redis):
        self.redis = redis
        self.logger = logger.bind(service="partner_auth")

    async def get_access_token(self) -> str:
        """
        Get cached or acquire new Partner Center access token

        Returns:
            str: Access token for Partner Center API

        Raises:
            PartnerCenterAuthError: If token acquisition fails
        """
        # 1. Check Redis cache
        cache_key = f"{self.CACHE_KEY_PREFIX}access"
        cached_token = await self.redis.get(cache_key)

        if cached_token:
            self.logger.debug("partner_token_cache_hit")
            return cached_token.decode()  # type: ignore[no-any-return]

        # 2. Acquire new token via MSAL
        self.logger.info("partner_token_acquiring")

        try:
            app = ConfidentialClientApplication(
                client_id=settings.PARTNER_CLIENT_ID,
                client_credential=settings.PARTNER_CLIENT_SECRET,
                authority=settings.PARTNER_AUTHORITY,
            )

            result = app.acquire_token_for_client(scopes=self.SCOPES)

            if "access_token" not in result:
                error_desc = result.get("error_description", "Unknown error")
                self.logger.error(
                    "partner_token_acquisition_failed",
                    error=result.get("error"),
                    error_description=error_desc,
                )
                raise PartnerCenterAuthError(
                    f"Failed to acquire Partner Center token: {error_desc}"
                )

            token = result["access_token"]
            expires_in = result.get("expires_in", 3600)

            # 3. Cache with TTL (expires_in - 5min safety margin)
            cache_ttl = max(expires_in - 300, 60)
            await self.redis.setex(cache_key, cache_ttl, token)

            self.logger.info(
                "partner_token_acquired", expires_in=expires_in, cache_ttl=cache_ttl
            )

            return token  # type: ignore[no-any-return]

        except Exception as e:
            self.logger.error("partner_token_error", error=str(e), exc_info=True)
            raise PartnerCenterAuthError(f"Token acquisition error: {str(e)}") from e

    async def invalidate_token(self) -> None:
        """Invalidate cached token (e.g., on 401/403 errors)"""
        cache_key = f"{self.CACHE_KEY_PREFIX}access"
        await self.redis.delete(cache_key)
        self.logger.info("partner_token_invalidated")
