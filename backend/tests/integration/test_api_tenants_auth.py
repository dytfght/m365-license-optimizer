"""
Integration tests for protected tenants endpoint
"""
from uuid import uuid4

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
        tenant_id = str(uuid4())
        tenant = TenantClient(
            tenant_id=tenant_id,
            name="Test Tenant",
            country="FR",
            default_language="fr",
            onboarding_status="active",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create a user
        password = "SecurePassword123!"
        user_principal_name = f"user_{uuid4()}@test.com"
        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=user_principal_name,
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
                "username": user_principal_name,
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

        # Check if our created tenant is in the list
        tenants = data["tenants"]
        found_tenant = next((t for t in tenants if t["tenant_id"] == tenant_id), None)
        assert found_tenant is not None
        assert found_tenant["name"] == "Test Tenant"
        assert found_tenant["country"] == "FR"
        assert found_tenant["default_language"] == "fr"

    @pytest.mark.asyncio
    async def test_list_tenants_with_invalid_token(self, client: AsyncClient):
        """Test tenants endpoint with invalid token"""
        response = await client.get(
            "/api/v1/tenants",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
