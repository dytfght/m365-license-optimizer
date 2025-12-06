"""
Unit tests for PartnerService
Tests API calls, pagination, retry logic, and caching
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio import Redis

from src.services.partner_auth_service import PartnerAuthService
from src.services.partner_service import PartnerCenterAPIError, PartnerService


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock(spec=Redis)
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    return redis


@pytest.fixture
def mock_auth_service():
    """Mock PartnerAuthService"""
    auth = AsyncMock(spec=PartnerAuthService)
    auth.get_access_token = AsyncMock(return_value="mock_token_123")
    auth.invalidate_token = AsyncMock()
    return auth


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def partner_service(mock_auth_service, mock_redis, mock_db_session):
    """Create PartnerService with mocks"""
    return PartnerService(
        auth_service=mock_auth_service, redis=mock_redis, db_session=mock_db_session
    )


class TestPartnerService:
    """Test suite for PartnerService"""

    @pytest.mark.asyncio
    async def test_fetch_pricing_success(self, partner_service, mock_redis):
        """Test successful pricing fetch"""
        mock_response = {
            "offers": [
                {"id": "SKU1", "name": "Office 365", "price": 10.0},
                {"id": "SKU2", "name": "Microsoft 365", "price": 15.0},
            ]
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)

            # session.get() returns a context manager, not a coroutine
            mock_get = MagicMock()
            mock_session.return_value.__aenter__.return_value.get = mock_get
            mock_get.return_value.__aenter__.return_value = mock_resp

            offers = await partner_service.fetch_pricing("FR")

            assert len(offers) == 2
            assert offers[0]["id"] == "SKU1"
            mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_pricing_from_cache(self, partner_service, mock_redis):
        """Test pricing retrieved from Redis cache"""
        import json

        cached_data = [{"id": "SKU1", "price": 10.0}]
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data).encode())

        offers = await partner_service.fetch_pricing("FR")

        assert len(offers) == 1
        assert offers[0]["id"] == "SKU1"

    @pytest.mark.asyncio
    async def test_fetch_pricing_401_invalidates_token(
        self, partner_service, mock_auth_service
    ):
        """Test 401 response invalidates token cache"""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 401

            mock_get = MagicMock()
            mock_session.return_value.__aenter__.return_value.get = mock_get
            mock_get.return_value.__aenter__.return_value = mock_resp

            with pytest.raises(Exception):
                await partner_service.fetch_pricing("FR")

            mock_auth_service.invalidate_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_pricing_429_rate_limit(self, partner_service):
        """Test 429 rate limit handling"""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 429
            mock_resp.headers = {"Retry-After": "60"}

            mock_get = MagicMock()
            mock_session.return_value.__aenter__.return_value.get = mock_get
            mock_get.return_value.__aenter__.return_value = mock_resp

            with pytest.raises(PartnerCenterAPIError) as exc_info:
                await partner_service.fetch_pricing("FR")

            assert "Rate limited" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_subscriptions_success(self, partner_service):
        """Test successful subscriptions fetch"""
        mock_response = {
            "items": [
                {"id": "sub1", "quantity": 10},
                {"id": "sub2", "quantity": 5},
            ]
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)

            mock_get = MagicMock()
            mock_session.return_value.__aenter__.return_value.get = mock_get
            mock_get.return_value.__aenter__.return_value = mock_resp

            subscriptions = await partner_service.fetch_subscriptions("customer123")

            assert len(subscriptions) == 2
            assert subscriptions[0]["id"] == "sub1"

    @pytest.mark.asyncio
    async def test_fetch_subscriptions_pagination(self, partner_service):
        """Test pagination handling in subscriptions"""
        page1 = {
            "items": [{"id": "sub1"}],
            "nextLink": "https://api.partnercenter.com/page2",
        }
        page2 = {
            "items": [{"id": "sub2"}],
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_resp1 = AsyncMock()
            mock_resp1.status = 200
            mock_resp1.json = AsyncMock(return_value=page1)

            mock_resp2 = AsyncMock()
            mock_resp2.status = 200
            mock_resp2.json = AsyncMock(return_value=page2)

            mock_get = MagicMock()
            mock_session.return_value.__aenter__.return_value.get = mock_get
            # Configure side_effect on the context manager's __aenter__
            # This simulates: async with session.get() as resp: -> resp is the result of __aenter__
            mock_get.return_value.__aenter__.side_effect = [mock_resp1, mock_resp2]

            subscriptions = await partner_service.fetch_subscriptions("customer123")

            assert len(subscriptions) == 2
