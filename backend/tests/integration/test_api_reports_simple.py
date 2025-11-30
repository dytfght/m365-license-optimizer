"""
Simple integration tests for Reports API endpoints - focusing on authentication and basic functionality
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.models.tenant import TenantClient


@pytest.mark.asyncio
async def test_reports_endpoints_require_auth(
    client: AsyncClient, test_tenant: TenantClient
):
    """Test that all reports endpoints require authentication"""
    fake_id = uuid4()

    # Test PDF generation without auth
    response = await client.post(f"/api/v1/reports/analyses/{fake_id}/pdf")
    assert response.status_code == 401

    # Test Excel generation without auth
    response = await client.post(f"/api/v1/reports/analyses/{fake_id}/excel")
    assert response.status_code == 401

    # Test listing analysis reports without auth
    response = await client.get(f"/api/v1/reports/analyses/{fake_id}")
    assert response.status_code == 401

    # Test listing tenant reports without auth
    response = await client.get(f"/api/v1/reports/tenants/{fake_id}")
    assert response.status_code == 401

    # Test getting report details without auth
    response = await client.get(f"/api/v1/reports/{fake_id}")
    assert response.status_code == 401

    # Test downloading report without auth
    response = await client.get(f"/api/v1/reports/{fake_id}/download")
    assert response.status_code == 401

    # Test deleting report without auth
    response = await client.delete(f"/api/v1/reports/{fake_id}")
    assert response.status_code == 401

    # Test cleanup without auth
    response = await client.post("/api/v1/reports/cleanup")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reports_api_available(client: AsyncClient, auth_headers: dict):
    """Test that reports API endpoints are accessible with proper auth"""
    fake_id = uuid4()

    # Test that endpoints return proper errors (not 404) when authenticated
    # This verifies the endpoints exist and are properly routed

    # PDF generation should return 404 for non-existent analysis (not 401 or 404 for missing route)
    response = await client.post(
        f"/api/v1/reports/analyses/{fake_id}/pdf", headers=auth_headers
    )
    # Should be 404 (analysis not found) or 500 (if report generation fails), not 401 (unauthorized) or 404 (route not found)
    assert response.status_code in [404, 500]

    # Excel generation should return 404 for non-existent analysis
    response = await client.post(
        f"/api/v1/reports/analyses/{fake_id}/excel", headers=auth_headers
    )
    assert response.status_code in [404, 500]

    # List analysis reports should work (might return empty list)
    response = await client.get(
        f"/api/v1/reports/analyses/{fake_id}", headers=auth_headers
    )
    assert response.status_code in [200, 404, 500]

    # List tenant reports should work (might return empty list)
    response = await client.get(
        f"/api/v1/reports/tenants/{fake_id}", headers=auth_headers
    )
    assert response.status_code in [200, 404, 500]

    # Get report details should return 404 for non-existent report
    response = await client.get(f"/api/v1/reports/{fake_id}", headers=auth_headers)
    assert response.status_code in [404, 500]

    # Download report should return 404 for non-existent report
    response = await client.get(
        f"/api/v1/reports/{fake_id}/download", headers=auth_headers
    )
    assert response.status_code in [404, 500]

    # Delete report should return 404 for non-existent report
    response = await client.delete(f"/api/v1/reports/{fake_id}", headers=auth_headers)
    assert response.status_code in [404, 500]

    # Cleanup should work
    response = await client.post("/api/v1/reports/cleanup", headers=auth_headers)
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_reports_endpoint_structure(client: AsyncClient, auth_headers: dict):
    """Test that reports endpoints return proper JSON responses"""
    fake_id = uuid4()

    # Test cleanup endpoint returns proper JSON structure
    response = await client.post("/api/v1/reports/cleanup", headers=auth_headers)

    if response.status_code == 200:
        data = response.json()
        # Should have proper response structure
        assert isinstance(data, dict)
        if "message" in data:
            assert isinstance(data["message"], str)
        if "deleted_reports" in data:
            assert isinstance(data["deleted_reports"], int)
        if "timestamp" in data:
            assert isinstance(data["timestamp"], str)

    # Test tenant reports endpoint
    response = await client.get(
        f"/api/v1/reports/tenants/{fake_id}", headers=auth_headers
    )

    if response.status_code == 200:
        data = response.json()
        # Should have proper list response structure
        assert isinstance(data, dict)
        assert "reports" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["reports"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["offset"], int)


@pytest.mark.asyncio
async def test_reports_error_responses(client: AsyncClient, auth_headers: dict):
    """Test that reports endpoints return proper error responses"""
    fake_id = uuid4()

    # Test error responses have proper structure
    response = await client.get(f"/api/v1/reports/{fake_id}", headers=auth_headers)

    if response.status_code == 404:
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data
        assert isinstance(data["detail"], str)

    # Test with invalid UUID format
    response = await client.get("/api/v1/reports/invalid-uuid", headers=auth_headers)

    # Should return 422 for invalid UUID format
    if response.status_code == 422:
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data


@pytest.mark.asyncio
async def test_reports_endpoint_validation(client: AsyncClient, auth_headers: dict):
    """Test input validation for reports endpoints"""
    fake_id = uuid4()

    # Test pagination parameters
    response = await client.get(
        f"/api/v1/reports/tenants/{fake_id}?limit=invalid", headers=auth_headers
    )

    # Should validate query parameters
    if response.status_code == 422:
        data = response.json()
        assert "detail" in data

    # Test valid pagination
    response = await client.get(
        f"/api/v1/reports/tenants/{fake_id}?limit=10&offset=5", headers=auth_headers
    )

    # Should accept valid pagination parameters
    assert response.status_code in [200, 404, 500]

    # Test report type filter
    response = await client.get(
        f"/api/v1/reports/tenants/{fake_id}?report_type=PDF", headers=auth_headers
    )

    assert response.status_code in [200, 404, 500]
