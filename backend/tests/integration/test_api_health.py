"""
Integration tests for health and version endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    """Integration tests for health check endpoints"""

    @pytest.mark.asyncio
    async def test_basic_health_check(self, client: AsyncClient):
        """Test basic /health endpoint"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client: AsyncClient):
        """Test detailed /api/v1/health endpoint with DB and Redis checks"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "redis" in data
        assert "version" in data

        # Database should be OK (test DB is running)
        assert data["database"] == "ok"

        # Overall status should be ok if both services are healthy
        if data["database"] == "ok" and data["redis"] == "ok":
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_version_endpoint(self, client: AsyncClient):
        """Test /api/v1/version endpoint"""
        response = await client.get("/api/v1/version")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "lot" in data
        assert "environment" in data

        # Check Lot 4 values
        assert data["version"] == "0.4.0"
        assert data["lot"] == 5
        assert data["name"] == "M365 License Optimizer"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root / endpoint returns API information"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "lot" in data
        assert "docs" in data
        assert "health" in data
        assert "api_base" in data

        assert data["version"] == "0.4.0"
        assert data["lot"] == 5
        assert data["api_base"] == "/api/v1"
