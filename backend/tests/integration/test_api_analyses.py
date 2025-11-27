"""
Integration tests for Analysis API endpoints
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from src.main import app
from src.models.tenant import TenantClient
from src.models.user import User, LicenseAssignment
from src.models.usage_metrics import UsageMetrics
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_analysis_success(client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session):
    """Test creating a new analysis successfully"""
    response = await client.post(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
        headers=auth_headers,
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "id" in data
    assert data["tenant_client_id"] == str(test_tenant.id)
    assert data["status"] in ["pending", "completed"]
    assert "summary" in data


@pytest.mark.asyncio
async def test_create_analysis_unauthorized(client: AsyncClient, test_tenant: TenantClient):
    """Test creating analysis without authentication"""
    response = await client.post(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_analysis_forbidden(client: AsyncClient, auth_headers: dict):
    """Test creating analysis for different tenant"""
    other_tenant_id = uuid4()
    
    response = await client.post(
        f"/api/v1/analyses/tenants/{other_tenant_id}/analyses",
        headers=auth_headers,
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_analyses(client: AsyncClient, auth_headers: dict, test_tenant: TenantClient):
    """Test listing analyses for a tenant"""
    # First create an analysis
    await client.post(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
        headers=auth_headers,
    )
    
    # Now list
    response = await client.get(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "analyses" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["analyses"]) >= 1


@pytest.mark.asyncio
async def test_get_analysis_details(client: AsyncClient, auth_headers: dict, test_tenant: TenantClient):
    """Test getting analysis details with recommendations"""
    # Create analysis
    create_response = await client.post(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
        headers=auth_headers,
    )
    analysis_id = create_response.json()["id"]
    
    # Get details
    response = await client.get(
        f"/api/v1/analyses/analyses/{analysis_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == analysis_id
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


@pytest.mark.asyncio
async def test_get_analysis_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting non-existent analysis"""
    fake_id = uuid4()
    
    response = await client.get(
        f"/api/v1/analyses/analyses/{fake_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_apply_recommendation_accept(client: AsyncClient, auth_headers: dict, test_tenant: TenantClient):
    """Test accepting a recommendation"""
    # Create analysis
    create_response = await client.post(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
        headers=auth_headers,
    )
    analysis_id = create_response.json()["id"]
    
    # Get recommendations
    details_response = await client.get(
        f"/api/v1/analyses/analyses/{analysis_id}",
        headers=auth_headers,
    )
    recommendations = details_response.json()["recommendations"]
    
    if recommendations:
        rec_id = recommendations[0]["id"]
        
        # Apply recommendation
        response = await client.post(
            f"/api/v1/analyses/recommendations/{rec_id}/apply",
            headers=auth_headers,
            json={"action": "accept"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recommendation_id"] == rec_id
        assert data["status"] == "accepted"
        assert "message" in data


@pytest.mark.asyncio
async def test_apply_recommendation_reject(client: AsyncClient, auth_headers: dict, test_tenant: TenantClient):
    """Test rejecting a recommendation"""
    # Create analysis
    create_response = await client.post(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
        headers=auth_headers,
    )
    analysis_id = create_response.json()["id"]
    
    # Get recommendations
    details_response = await client.get(
        f"/api/v1/analyses/analyses/{analysis_id}",
        headers=auth_headers,
    )
    recommendations = details_response.json()["recommendations"]
    
    if recommendations:
        rec_id = recommendations[0]["id"]
        
        # Reject recommendation
        response = await client.post(
            f"/api/v1/analyses/recommendations/{rec_id}/apply",
            headers=auth_headers,
            json={"action": "reject"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recommendation_id"] == rec_id
        assert data["status"] == "rejected"


@pytest.mark.asyncio
async def test_apply_recommendation_invalid_action(client: AsyncClient, auth_headers: dict, test_tenant: TenantClient):
    """Test applying recommendation with invalid action"""
    rec_id = uuid4()
    
    response = await client.post(
        f"/api/v1/analyses/recommendations/{rec_id}/apply",
        headers=auth_headers,
        json={"action": "invalid"},
    )
    
    # Should fail validation
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_apply_recommendation_not_found(client: AsyncClient, auth_headers: dict):
    """Test applying non-existent recommendation"""
    fake_id = uuid4()
    
    response = await client.post(
        f"/api/v1/analyses/recommendations/{fake_id}/apply",
        headers=auth_headers,
        json={"action": "accept"},
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analysis_with_inactive_users(client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session):
    """Test analysis identifies inactive users"""
    # Create an inactive user
    from src.repositories.user_repository import UserRepository
    user_repo = UserRepository(db_session)
    
    user = await user_repo.create(
        graph_id=str(uuid4()),
        tenant_client_id=test_tenant.id,
        user_principal_name="inactive@test.com",
        account_enabled=False,
    )
    
    # Assign a license
    license = LicenseAssignment(
        user_id=user.id,
        sku_id="06ebc4ee-1bb5-47dd-8120-11324bc54e06",  # E5
    )
    db_session.add(license)
    await db_session.commit()
    
    # Run analysis
    response = await client.post(
        f"/api/v1/analyses/tenants/{test_tenant.id}/analyses",
        headers=auth_headers,
    )
    
    assert response.status_code == 201
    analysis_id = response.json()["id"]
    
    # Get details
    details = await client.get(
        f"/api/v1/analyses/analyses/{analysis_id}",
        headers=auth_headers,
    )
    
    recommendations = details.json()["recommendations"]
    
    # Should have recommendation to remove license
    inactive_recs = [r for r in recommendations if "disabled" in r["reason"].lower() or "inactive" in r["reason"].lower()]
    assert len(inactive_recs) > 0
