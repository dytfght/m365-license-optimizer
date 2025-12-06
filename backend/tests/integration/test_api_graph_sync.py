"""
Integration tests for Graph API endpoints (LOT4)
Tests for /api/v1/tenants/{tenant_id}/sync_* endpoints
NOTE: These endpoints may not be fully implemented yet.
These are placeholder tests to be enabled once endpoints are complete.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestGraphSyncEndpoints:
    """Integration tests for Microsoft Graph sync endpoints"""

    @pytest.mark.asyncio
    async def test_sync_users_unauthorized(self, client: AsyncClient):
        """Test sync_users without authentication"""
        tenant_id = str(uuid4())

        response = await client.post(
            f"/api/v1/tenants/{tenant_id}/sync_users",
            json={"force_refresh": False},
        )

        assert response.status_code == 401

    # TODO: Re-enable these tests once sync endpoints are confirmed to exist
    # and their exact signatures/dependencies are verified

    # @pytest.mark.asyncio
    # async def test_sync_users_success(self, client: AsyncClient, db_session: AsyncSession):
    #     """Test successful users synchronization"""
    #     # ... implementation
    #     pass

    # @pytest.mark.asyncio
    # async def test_sync_licenses_success(self, client: AsyncClient, db_session: AsyncSession):
    #     """Test successful licenses synchronization"""
    #     # ... implementation
    #     pass

    # @pytest.mark.asyncio
    # async def test_sync_usage_success(self, client: AsyncClient, db_session: AsyncSession):
    #     """Test successful usage metrics synchronization"""
    #     # ...implementation
    #     pass
