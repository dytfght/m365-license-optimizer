"""
GR01: Microsoft Graph authentication service
Handles client credentials flow for tenant app registrations
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

import aiohttp
import structlog

from src.core.config import settings
from .exceptions import GraphAuthError

logger = structlog.get_logger(__name__)


class GraphAuthService:
    """
    Service for obtaining Microsoft Graph access tokens using client credentials flow.
    Implements token caching with automatic refresh.
    """

    def __init__(self):
        self._token_cache: dict[str, dict] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_cache_key(self, tenant_id: str, client_id: str) -> str:
        """Generate cache key for token"""
        return f"{tenant_id}:{client_id}"

    def _is_token_valid(self, cached_token: Optional[dict]) -> bool:
        """Check if cached token is still valid (with 5 min buffer)"""
        if not cached_token:
            return False

        expires_at = cached_token.get("expires_at")
        if not expires_at:
            return False

        # Refresh if less than 5 minutes remaining
        buffer = timedelta(minutes=5)
        # ← CORRECTION : Utiliser datetime.now(timezone.utc)
        return datetime.now(timezone.utc) + buffer < expires_at

    async def get_token(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: Optional[str] = None,
    ) -> str:
        """
        Get access token for Microsoft Graph API using client credentials flow.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            client_secret: Client secret
            scope: OAuth scope (default: https://graph.microsoft.com/.default)

        Returns:
            Access token string

        Raises:
            GraphAuthError: If authentication fails
        """
        cache_key = self._get_cache_key(tenant_id, client_id)

        # Check cache
        cached = self._token_cache.get(cache_key)
        if cached and self._is_token_valid(cached):
            logger.debug(
                "graph_token_cache_hit", tenant_id=tenant_id, client_id=client_id
            )
            return cached["access_token"]

        # Request new token
        scope = scope or settings.GRAPH_API_SCOPES
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        }

        session = await self._get_session()

        try:
            async with session.post(token_url, data=data) as resp:
                if resp.status != 200:
                    error_data = await resp.json()
                    error_msg = error_data.get("error_description", "Unknown error")
                    logger.error(
                        "graph_auth_failed",
                        tenant_id=tenant_id,
                        client_id=client_id,
                        status_code=resp.status,
                        error=error_msg,
                    )
                    raise GraphAuthError(
                        f"Authentication failed: {error_msg}",
                        status_code=resp.status,
                        response_data=error_data,
                    )

                result = await resp.json()
                access_token = result["access_token"]
                expires_in = result.get("expires_in", 3600)

                # Cache token
                # ← CORRECTION : Utiliser datetime.now(timezone.utc)
                self._token_cache[cache_key] = {
                    "access_token": access_token,
                    "expires_at": datetime.now(timezone.utc)
                    + timedelta(seconds=expires_in),
                }

                logger.info(
                    "graph_token_acquired",
                    tenant_id=tenant_id,
                    client_id=client_id,
                    expires_in=expires_in,
                )

                return access_token

        except aiohttp.ClientError as e:
            logger.error("graph_auth_request_failed", tenant_id=tenant_id, error=str(e))
            raise GraphAuthError(f"Network error during authentication: {str(e)}")

    def clear_cache(
        self, tenant_id: Optional[str] = None, client_id: Optional[str] = None
    ):
        """
        Clear token cache.

        Args:
            tenant_id: If provided, clear only this tenant
            client_id: If provided (with tenant_id), clear only this specific app
        """
        if tenant_id and client_id:
            cache_key = self._get_cache_key(tenant_id, client_id)
            self._token_cache.pop(cache_key, None)
            logger.info(
                "graph_token_cache_cleared", tenant_id=tenant_id, client_id=client_id
            )
        elif tenant_id:
            keys_to_remove = [
                k for k in self._token_cache.keys() if k.startswith(f"{tenant_id}:")
            ]
            for key in keys_to_remove:
                self._token_cache.pop(key, None)
            logger.info(
                "graph_token_cache_cleared_tenant",
                tenant_id=tenant_id,
                count=len(keys_to_remove),
            )
        else:
            self._token_cache.clear()
            logger.info("graph_token_cache_cleared_all")
