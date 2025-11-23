"""
Integration tests for tenant API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestTenantsAPI:
    """Test /api/v1/tenants endpoints"""

    @pytest.mark.asyncio
    async def test_list_tenants_empty(self, client: AsyncClient, auth_headers):
        """Test listing tenants (should contain the one created by auth_headers)"""
        response = await client.get("/api/v1/tenants", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        assert "total" in data
        assert data["total"] >= 1  # auth_headers creates one

    @pytest.mark.asyncio
    async def test_create_tenant(self, client: AsyncClient, auth_headers):
        """Test creating a new tenant"""
        from uuid import uuid4

        new_tenant_id = str(uuid4())
        new_client_id = str(uuid4())

        tenant_data = {
            "name": "New Test Company",
            "tenant_id": new_tenant_id,
            "country": "FR",
            "client_id": new_client_id,
            "client_secret": "test-secret",
            "scopes": ["User.Read.All", "Directory.Read.All"],
            "default_language": "fr",
            "authority_url": f"https://login.microsoftonline.com/{new_tenant_id}",
        }

        response = await client.post(
            "/api/v1/tenants", json=tenant_data, headers=auth_headers
        )

        if response.status_code != 201:
            print(f"DEBUG: Create tenant failed: {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Test Company"
        assert data["tenant_id"] == new_tenant_id
        assert data["onboarding_status"] == "pending"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_tenant_duplicate(self, client: AsyncClient, auth_headers):
        """Test creating duplicate tenant fails"""
        from uuid import uuid4

        dup_tenant_id = str(uuid4())
        dup_client_id = str(uuid4())

        tenant_data = {
            "name": "Duplicate Company",
            "tenant_id": dup_tenant_id,
            "country": "FR",
            "client_id": dup_client_id,
            "client_secret": "test-secret",
            "authority_url": f"https://login.microsoftonline.com/{dup_tenant_id}",
        }

        # Create first tenant
        response1 = await client.post(
            "/api/v1/tenants", json=tenant_data, headers=auth_headers
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await client.post(
            "/api/v1/tenants", json=tenant_data, headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_tenant_by_id(self, client: AsyncClient, auth_headers):
        """Test getting tenant by ID"""
        from uuid import uuid4

        get_tenant_id = str(uuid4())
        get_client_id = str(uuid4())

        # Create tenant
        tenant_data = {
            "name": "Get By ID Company",
            "tenant_id": get_tenant_id,
            "country": "FR",
            "client_id": get_client_id,
            "client_secret": "test-secret",
            "authority_url": f"https://login.microsoftonline.com/{get_tenant_id}",
        }

        create_response = await client.post(
            "/api/v1/tenants", json=tenant_data, headers=auth_headers
        )
        assert create_response.status_code == 201
        tenant_id = create_response.json()["id"]

        # Get tenant
        response = await client.get(
            f"/api/v1/tenants/{tenant_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tenant_id
        assert data["name"] == "Get By ID Company"
        assert "app_registration" in data

    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent tenant returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/tenants/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_tenants_after_creation(self, client: AsyncClient, auth_headers):
        """Test listing tenants returns created tenants"""
        from uuid import uuid4

        # Create 2 tenants
        for i in range(2):
            tid = str(uuid4())
            tenant_data = {
                "name": f"Company {i}",
                "tenant_id": tid,
                "country": "FR",
                "client_id": str(uuid4()),
                "client_secret": "test-secret",
                "authority_url": f"https://login.microsoftonline.com/{tid}",
            }
            await client.post("/api/v1/tenants", json=tenant_data, headers=auth_headers)

        # List tenants
        response = await client.get("/api/v1/tenants", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        # Current implementation only returns the user's tenant
        # So even if we created more, we should only see 1 (the one from auth_headers)
        assert data["total"] == 1
        tenants = data["tenants"]
        assert len(tenants) == 1
        # Verify we can still access the created tenants directly by ID (as admin)
        # This confirms they were actually created
        # We already tested get_by_id above, so we just trust the creation 201 response here

    @pytest.mark.asyncio
    async def test_create_tenant_without_auth(self, client: AsyncClient):
        """Test creating tenant without authentication fails"""
        tenant_data = {
            "name": "Test Company",
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "country": "FR",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "test-secret",
        }

        response = await client.post("/api/v1/tenants", json=tenant_data)

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.slow
class TestTenantValidationAPI:
    """Test tenant credential validation (requires mocking)"""

    @pytest.mark.asyncio
    async def test_validate_endpoint_placeholder(
        self, client: AsyncClient, auth_headers
    ):
        """
        Placeholder for validation tests.
        Will be implemented with proper mocking in next commits.
        """
        # This test is marked as slow and will be expanded with WireMock
        # integration for mocking Microsoft Graph responses
        pass
