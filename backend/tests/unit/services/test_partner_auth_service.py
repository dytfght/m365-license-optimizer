"""
Unit tests for PartnerAuthService
Tests MSAL authentication, Redis caching, and error handling
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio import Redis

from src.services.partner_auth_service import PartnerAuthService, PartnerCenterAuthError


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock(spec=Redis)
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def auth_service(mock_redis):
    """Create PartnerAuthService with mocked Redis"""
    return PartnerAuthService(redis=mock_redis)


class TestPartnerAuthService:
    """Test suite for PartnerAuthService"""

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, auth_service, mock_redis):
        """Test successful token acquisition"""
        with patch(
            "src.services.partner_auth_service.ConfidentialClientApplication"
        ) as mock_app:
            mock_instance = MagicMock()
            mock_instance.acquire_token_for_client.return_value = {
                "access_token": "test_token_123",
                "expires_in": 3600,
            }
            mock_app.return_value = mock_instance

            token = await auth_service.get_access_token()

            assert token == "test_token_123"
            mock_redis.setex.assert_called_once()
            # Verify cache TTL is expires_in - 300 (5min safety margin)
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 3300  # 3600 - 300

    @pytest.mark.asyncio
    async def test_get_access_token_from_cache(self, auth_service, mock_redis):
        """Test token retrieval from Redis cache"""
        mock_redis.get = AsyncMock(return_value=b"cached_token_456")

        token = await auth_service.get_access_token()

        assert token == "cached_token_456"
        mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_access_token_msal_error(self, auth_service, mock_redis):
        """Test handling of MSAL error"""
        with patch(
            "src.services.partner_auth_service.ConfidentialClientApplication"
        ) as mock_app:
            mock_instance = MagicMock()
            mock_instance.acquire_token_for_client.return_value = {
                "error": "invalid_client",
                "error_description": "Invalid client credentials",
            }
            mock_app.return_value = mock_instance

            with pytest.raises(PartnerCenterAuthError) as exc_info:
                await auth_service.get_access_token()

            assert "Invalid client credentials" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_access_token_exception(self, auth_service, mock_redis):
        """Test handling of unexpected exception"""
        with patch(
            "src.services.partner_auth_service.ConfidentialClientApplication"
        ) as mock_app:
            mock_app.side_effect = Exception("Network error")

            with pytest.raises(PartnerCenterAuthError) as exc_info:
                await auth_service.get_access_token()

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalidate_token(self, auth_service, mock_redis):
        """Test token cache invalidation"""
        await auth_service.invalidate_token()

        mock_redis.delete.assert_called_once_with("partner_token:access")

    @pytest.mark.asyncio
    async def test_cache_ttl_minimum(self, auth_service, mock_redis):
        """Test cache TTL has minimum of 60s even with low expires_in"""
        with patch(
            "src.services.partner_auth_service.ConfidentialClientApplication"
        ) as mock_app:
            mock_instance = MagicMock()
            mock_instance.acquire_token_for_client.return_value = {
                "access_token": "test_token",
                "expires_in": 100,  # Low value
            }
            mock_app.return_value = mock_instance

            await auth_service.get_access_token()

            call_args = mock_redis.setex.call_args
            # Should be max(100 - 300, 60) = 60
            assert call_args[0][1] == 60
