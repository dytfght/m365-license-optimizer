"""
Integration tests for Microsoft Graph services
(These tests use mocks - real Graph API tests will use WireMock in later commits)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.integrations.graph import GraphAuthService, GraphClient
from src.integrations.graph.exceptions import GraphAuthError, GraphThrottlingError


@pytest.mark.integration
class TestGraphAuthService:
    """Test GraphAuthService with mocks"""
    
    @pytest.mark.asyncio
    async def test_get_token_success(self):
        """Test successful token acquisition"""
        service = GraphAuthService()
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "access_token": "test-token-123",
            "expires_in": 3600,
        })
        
        with patch.object(service, '_get_session') as mock_session:
            mock_session.return_value.post = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
            )
            
            token = await service.get_token(
                tenant_id="test-tenant",
                client_id="test-client",
                client_secret="test-secret"
            )
            
            assert token == "test-token-123"
    
    @pytest.mark.asyncio
    async def test_get_token_cached(self):
        """Test token caching"""
        service = GraphAuthService()
        
        # Manually set cache
        cache_key = service._get_cache_key("test-tenant", "test-client")
        from datetime import datetime, timedelta
        service._token_cache[cache_key] = {
            "access_token": "cached-token",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
        }
        
        # Should return cached token without API call
        token = await service.get_token(
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret="test-secret"
        )
        
        assert token == "cached-token"
    
    @pytest.mark.asyncio
    async def test_get_token_auth_error(self):
        """Test authentication error"""
        service = GraphAuthService()
        
        mock_response = MagicMock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={
            "error": "invalid_client",
            "error_description": "Invalid client secret"
        })
        
        with patch.object(service, '_get_session') as mock_session:
            mock_session.return_value.post = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
            )
            
            with pytest.raises(GraphAuthError) as exc_info:
                await service.get_token(
                    tenant_id="test-tenant",
                    client_id="test-client",
                    client_secret="wrong-secret"
                )
            
            assert "Invalid client secret" in str(exc_info.value)


@pytest.mark.integration
class TestGraphClient:
    """Test GraphClient with mocks"""
    
    @pytest.mark.asyncio
    async def test_get_users_success(self):
        """Test fetching users"""
        client = GraphClient(access_token="test-token")
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "value": [
                {"id": "user1", "userPrincipalName": "user1@test.com"},
                {"id": "user2", "userPrincipalName": "user2@test.com"},
            ]
        })
        
        with patch.object(client, '_get_session') as mock_session:
            mock_session.return_value.get = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
            )
            
            users = await client.get_users()
            
            assert len(users) == 2
            assert users[0]["id"] == "user1"
    
    @pytest.mark.asyncio
    async def test_get_paginated_multiple_pages(self):
        """Test pagination with multiple pages"""
        client = GraphClient(access_token="test-token")
        
        # First page
        mock_response1 = MagicMock()
        mock_response1.status = 200
        mock_response1.json = AsyncMock(return_value={
            "value": [{"id": "user1"}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/users?$skip=1"
        })
        
        # Second page
        mock_response2 = MagicMock()
        mock_response2.status = 200
        mock_response2.json = AsyncMock(return_value={
            "value": [{"id": "user2"}],
        })
        
        with patch.object(client, '_get_session') as mock_session:
            mock_session.return_value.get = AsyncMock(
                side_effect=[
                    AsyncMock(__aenter__=AsyncMock(return_value=mock_response1)),
                    AsyncMock(__aenter__=AsyncMock(return_value=mock_response2)),
                ]
            )
            
            items = await client.get_paginated("/users")
            
            assert len(items) == 2
            assert items[0]["id"] == "user1"
            assert items[1]["id"] == "user2"
    
    @pytest.mark.asyncio
    async def test_throttling_retry(self):
        """Test retry on throttling"""
        client = GraphClient(access_token="test-token")
        
        # First call: throttled
        mock_response_429 = MagicMock()
        mock_response_429.status = 429
        mock_response_429.headers = {"Retry-After": "2"}
        
        # Second call: success
        mock_response_200 = MagicMock()
        mock_response_200.status = 200
        mock_response_200.json = AsyncMock(return_value={"value": []})
        
        with patch.object(client, '_get_session') as mock_session:
            mock_session.return_value.get = AsyncMock(
                side_effect=[
                    AsyncMock(__aenter__=AsyncMock(return_value=mock_response_429)),
                    AsyncMock(__aenter__=AsyncMock(return_value=mock_response_200)),
                ]
            )
            
            # Should retry and succeed
            items = await client.get_paginated("/users")
            
            assert len(items) == 0
