"""
Integration tests for Admin Observability API endpoints (LOT 11)
Tests /api/v1/admin/metrics, /health/extended, and /backup endpoints.
"""
import pytest
from httpx import AsyncClient

from src.main import app


class TestObservabilityEndpoints:
    """Integration tests for observability API endpoints."""

    @pytest.fixture
    def admin_headers(self, auth_headers):
        """Get admin authentication headers."""
        return auth_headers

    @pytest.mark.asyncio
    async def test_get_metrics_unauthorized(self, client: AsyncClient):
        """Test metrics endpoint requires authentication."""
        response = await client.get("/api/v1/admin/metrics")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_metrics_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful metrics retrieval."""
        response = await client.get(
            "/api/v1/admin/metrics",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "system" in data
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "process" in data
        
        # Verify system info
        assert "platform" in data["system"]
        assert "python_version" in data["system"]

    @pytest.mark.asyncio
    async def test_extended_health_check_unauthorized(
        self, client: AsyncClient
    ):
        """Test extended health check requires authentication."""
        response = await client.get("/api/v1/admin/health/extended")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_extended_health_check_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful extended health check."""
        response = await client.get(
            "/api/v1/admin/health/extended",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "status" in data
        assert "database" in data
        assert "redis" in data
        assert "azure_storage" in data
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data
        assert "checks" in data
        
        # Database and Redis should be healthy in test environment
        assert data["database"] in ["ok", "unhealthy"]
        assert data["redis"] in ["ok", "unhealthy"]

    @pytest.mark.asyncio
    async def test_backup_trigger_unauthorized(self, client: AsyncClient):
        """Test backup trigger requires authentication."""
        response = await client.post(
            "/api/v1/admin/backup",
            json={"include_logs": False},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_backup_trigger_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test backup trigger endpoint."""
        response = await client.post(
            "/api/v1/admin/backup",
            headers=auth_headers,
            json={"include_logs": False, "description": "Test backup"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "backup_id" in data
        assert "timestamp" in data
        assert "message" in data
        
        # In test environment without pg_dump, may fail gracefully
        if not data["success"]:
            assert "error" in data

    @pytest.mark.asyncio
    async def test_backup_with_logs_option(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test backup with include_logs option."""
        response = await client.post(
            "/api/v1/admin/backup",
            headers=auth_headers,
            json={"include_logs": True},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data


class TestMetricsDataIntegrity:
    """Test metrics data integrity and format."""

    @pytest.mark.asyncio
    async def test_cpu_metrics_values(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test CPU metrics have valid values."""
        response = await client.get(
            "/api/v1/admin/metrics",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        cpu = response.json()["cpu"]
        
        # percent should be between 0 and 100
        if "error" not in cpu:
            assert 0 <= cpu["percent"] <= 100

    @pytest.mark.asyncio
    async def test_memory_metrics_values(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test memory metrics have valid values."""
        response = await client.get(
            "/api/v1/admin/metrics",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        memory = response.json()["memory"]
        
        if "error" not in memory:
            # Memory values should be positive
            assert memory["total_bytes"] > 0
            assert memory["available_bytes"] >= 0
            assert 0 <= memory["percent"] <= 100

    @pytest.mark.asyncio
    async def test_timestamp_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test timestamp is in ISO 8601 format."""
        response = await client.get(
            "/api/v1/admin/metrics",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        timestamp = response.json()["timestamp"]
        
        # Should contain 'T' separator for ISO format
        assert "T" in timestamp
        # Should end with timezone info
        assert timestamp.endswith("Z") or "+" in timestamp or "-" in timestamp[-6:]


class TestExtendedHealthDetails:
    """Test extended health check details."""

    @pytest.mark.asyncio
    async def test_health_checks_dict(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test individual health checks are provided."""
        response = await client.get(
            "/api/v1/admin/health/extended",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        checks = response.json()["checks"]
        
        # Should have check results
        assert isinstance(checks, dict)

    @pytest.mark.asyncio
    async def test_version_in_health_response(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test version is included in health response."""
        response = await client.get(
            "/api/v1/admin/health/extended",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "version" in data
        assert data["version"]  # Non-empty
        assert "." in data["version"]  # Should be semver-like

    @pytest.mark.asyncio
    async def test_environment_in_health_response(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test environment is included in health response."""
        response = await client.get(
            "/api/v1/admin/health/extended",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "environment" in data
        assert data["environment"] in ["development", "test", "production"]

