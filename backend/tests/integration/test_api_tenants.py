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
        """Test listing tenants when none exist"""
        response = await client.get("/api/v1/tenants", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_create_tenant(self, client: AsyncClient, auth_headers):
        """Test creating a new tenant"""
        tenant_data = {
            "name": "Test Company",
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "country": "FR",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "test-secret",
            "scopes": ["User.Read.All", "Directory.Read.All"],
            "default_language": "fr",
        }
        
        response = await client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Company"
        assert data["tenant_id"] == "12345678-1234-1234-1234-123456789012"
        assert data["status"] == "pending"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_tenant_duplicate(self, client: AsyncClient, auth_headers):
        """Test creating duplicate tenant fails"""
        tenant_data = {
            "name": "Test Company",
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "country": "FR",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "test-secret",
        }
        
        # Create first tenant
        response1 = await client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = await client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_tenant_by_id(self, client: AsyncClient, auth_headers):
        """Test getting tenant by ID"""
        # Create tenant
        tenant_data = {
            "name": "Test Company",
            "tenant_id": "12345678-1234-1234-1234-123456789012",
            "country": "FR",
            "client_id": "87654321-4321-4321-4321-210987654321",
            "client_secret": "test-secret",
        }
        
        create_response = await client.post(
            "/api/v1/tenants",
            json=tenant_data,
            headers=auth_headers
        )
        tenant_id = create_response.json()["id"]
        
        # Get tenant
        response = await client.get(
            f"/api/v1/tenants/{tenant_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tenant_id
        assert data["name"] == "Test Company"
        assert "app_registration" in data
    
    @pytest.mark.asyncio
    async def test_get_tenant_not_found(self, client: AsyncClient, auth_headers):
        """Test getting non-existent tenant returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = await client.get(
            f"/api/v1/tenants/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_tenants_after_creation(self, client: AsyncClient, auth_headers):
        """Test listing tenants returns created tenants"""
        # Create 2 tenants
        for i in range(2):
            tenant_data = {
                "name": f"Company {i}",
                "tenant_id": f"1234567{i}-1234-1234-1234-123456789012",
                "country": "FR",
                "client_id": f"8765432{i}-4321-4321-4321-210987654321",
                "client_secret": "test-secret",
            }
            await client.post("/api/v1/tenants", json=tenant_data, headers=auth_headers)
        
        # List tenants
        response = await client.get("/api/v1/tenants", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(t["name"] == "Company 0" for t in data)
        assert any(t["name"] == "Company 1" for t in data)
    
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
    async def test_validate_endpoint_placeholder(self, client: AsyncClient, auth_headers):
        """
        Placeholder for validation tests.
        Will be implemented with proper mocking in next commits.
        """
        # This test is marked as slow and will be expanded with WireMock
        # integration for mocking Microsoft Graph responses
        pass
