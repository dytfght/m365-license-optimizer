"""
Integration tests for protected tenants endpoint
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.models.tenant import TenantClient
from src.models.user import User


@pytest.mark.integration
class TestTenantsEndpoint:
    """Integration tests for tenants list endpoint"""

    @pytest.mark.asyncio
    async def test_list_tenants_without_auth(self, client: AsyncClient):
        """Test that tenants endpoint requires authentication"""
        response = await client.get("/api/v1/tenants")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_tenants_with_auth(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test listing tenants with valid authentication"""
        # Create a tenant
        tenant = TenantClient(
            tenant_id="test-tenant-123",
            name="Test Tenant",
            country="FR",
            default_language="fr",
            onboarding_status="active",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create a user
        password = "SecurePassword123!"
        user = User(
            graph_id="user-graph-123",
            tenant_client_id=tenant.id,
            user_principal_name="user@test.com",
            display_name="Test User",
            account_enabled=True,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()

        # Login to get access token
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@test.com",
                "password": password,
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Test tenants list with auth
        response = await client.get(
            "/api/v1/tenants",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert "total" in data
        assert data["total"] >= 1

        # Check tenant data
        tenant_data = data["tenants"][0]
        assert tenant_data["name"] == "Test Tenant"
        assert tenant_data["tenant_id"] == "test-tenant-123"
        assert tenant_data["country"] == "FR"
        assert tenant_data["default_language"] == "fr"

    @pytest.mark.asyncio
    async def test_list_tenants_with_invalid_token(self, client: AsyncClient):
        """Test tenants endpoint with invalid token"""
        response = await client.get(
            "/api/v1/tenants",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
