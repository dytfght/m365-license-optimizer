"""
Integration tests for Reports API endpoints
"""
from datetime import datetime, timedelta
from uuid import uuid4
import pytest
from httpx import AsyncClient

from src.models.tenant import TenantClient
from src.models.analysis import Analysis


@pytest.mark.asyncio
async def test_generate_pdf_report_success(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test generating PDF report successfully"""
    # First create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate PDF report
    response = await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/pdf",
        headers=auth_headers,
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "id" in data
    assert data["analysis_id"] == str(analysis.id)
    assert data["tenant_client_id"] == str(test_tenant.id)
    assert data["report_type"] == "PDF"
    assert data["file_name"].endswith(".pdf")
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] > 0
    assert data["generated_by"] == "test@example.com"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_generate_excel_report_success(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test generating Excel report successfully"""
    # First create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate Excel report
    response = await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/excel",
        headers=auth_headers,
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "id" in data
    assert data["analysis_id"] == str(analysis.id)
    assert data["tenant_client_id"] == str(test_tenant.id)
    assert data["report_type"] == "EXCEL"
    assert data["file_name"].endswith(".xlsx")
    assert data["mime_type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert data["file_size"] > 0
    assert data["generated_by"] == "test@example.com"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_generate_report_analysis_not_found(
    client: AsyncClient, auth_headers: dict
):
    """Test generating report for non-existent analysis"""
    fake_analysis_id = uuid4()
    
    response = await client.post(
        f"/api/v1/reports/analyses/{fake_analysis_id}/pdf",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Analysis not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_report_unauthorized(
    client: AsyncClient, test_tenant: TenantClient
):
    """Test generating report without authentication"""
    fake_analysis_id = uuid4()
    
    response = await client.post(
        f"/api/v1/reports/analyses/{fake_analysis_id}/pdf"
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_analysis_reports(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test listing reports for an analysis"""
    # Create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate a couple of reports
    await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/pdf",
        headers=auth_headers,
    )
    await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/excel",
        headers=auth_headers,
    )
    
    # List reports for the analysis
    response = await client.get(
        f"/api/v1/reports/analyses/{analysis.id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "reports" in data
    assert "total" in data
    assert data["total"] >= 2
    assert len(data["reports"]) >= 2
    assert data["limit"] == 50
    assert data["offset"] == 0
    
    # Verify report types
    report_types = [report["report_type"] for report in data["reports"]]
    assert "PDF" in report_types
    assert "EXCEL" in report_types


@pytest.mark.asyncio
async def test_list_tenant_reports(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test listing reports for a tenant"""
    # Create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate a report
    await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/pdf",
        headers=auth_headers,
    )
    
    # List reports for the tenant
    response = await client.get(
        f"/api/v1/reports/tenants/{test_tenant.id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "reports" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["reports"]) >= 1
    
    # Verify all reports belong to this tenant
    for report in data["reports"]:
        assert report["tenant_client_id"] == str(test_tenant.id)


@pytest.mark.asyncio
async def test_list_tenant_reports_with_filter(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test listing reports for a tenant with type filter"""
    # Create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate both PDF and Excel reports
    await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/pdf",
        headers=auth_headers,
    )
    await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/excel",
        headers=auth_headers,
    )
    
    # List only PDF reports
    response = await client.get(
        f"/api/v1/reports/tenants/{test_tenant.id}?report_type=PDF",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify only PDF reports are returned
    for report in data["reports"]:
        assert report["report_type"] == "PDF"


@pytest.mark.asyncio
async def test_get_report_details(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test getting report details"""
    # Create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate a report
    create_response = await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/pdf",
        headers=auth_headers,
    )
    report_id = create_response.json()["id"]
    
    # Get report details
    response = await client.get(
        f"/api/v1/reports/{report_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == report_id
    assert data["analysis_id"] == str(analysis.id)
    assert data["tenant_client_id"] == str(test_tenant.id)
    assert data["report_type"] == "PDF"
    assert "file_name" in data
    assert "file_size" in data
    assert "mime_type" in data
    assert "created_at" in data
    assert data["generated_by"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_report_not_found(
    client: AsyncClient, auth_headers: dict
):
    """Test getting non-existent report"""
    fake_report_id = uuid4()
    
    response = await client.get(
        f"/api/v1/reports/{fake_report_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Report not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_download_report(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test getting download information for a report"""
    # Create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate a report
    create_response = await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/pdf",
        headers=auth_headers,
    )
    report_id = create_response.json()["id"]
    
    # Get download information
    response = await client.get(
        f"/api/v1/reports/{report_id}/download",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["report_id"] == report_id
    assert "file_name" in data
    assert "file_size" in data
    assert data["mime_type"] == "application/pdf"
    assert "download_url" in data
    assert data["download_url"].endswith("/file")


@pytest.mark.asyncio
async def test_download_expired_report(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test downloading an expired report"""
    from src.models.report import Report
    
    # Create an expired report directly in database
    expired_report = Report(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        report_type="PDF",
        file_name="expired_report.pdf",
        file_path="/tmp/expired_report.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        generated_by="test@example.com",
        created_at=datetime.utcnow() - timedelta(days=30),
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
    )
    db_session.add(expired_report)
    await db_session.commit()
    
    # Try to download expired report
    response = await client.get(
        f"/api/v1/reports/{expired_report.id}/download",
        headers=auth_headers,
    )
    
    assert response.status_code == 404  # Not found (expired reports are treated as not found)


@pytest.mark.asyncio
async def test_delete_report(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test deleting (soft deleting) a report"""
    # Create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate a report
    create_response = await client.post(
        f"/api/v1/reports/analyses/{analysis.id}/pdf",
        headers=auth_headers,
    )
    report_id = create_response.json()["id"]
    
    # Delete the report
    response = await client.delete(
        f"/api/v1/reports/{report_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 204  # No content
    
    # Verify report is no longer accessible
    get_response = await client.get(
        f"/api/v1/reports/{report_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_report(
    client: AsyncClient, auth_headers: dict
):
    """Test deleting non-existent report"""
    fake_report_id = uuid4()
    
    response = await client.delete(
        f"/api/v1/reports/{fake_report_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Report not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cleanup_expired_reports(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test cleaning up expired reports"""
    from src.models.report import Report
    
    # Create some expired reports directly in database
    for i in range(3):
        expired_report = Report(
            id=uuid4(),
            tenant_client_id=test_tenant.id,
            report_type="PDF",
            file_name=f"expired_report_{i}.pdf",
            file_path=f"/tmp/expired_report_{i}.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
            generated_by="test@example.com",
            created_at=datetime.utcnow() - timedelta(days=30),
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
        )
        db_session.add(expired_report)
    
    # Create a non-expired report
    valid_report = Report(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        report_type="PDF",
        file_name="valid_report.pdf",
        file_path="/tmp/valid_report.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        generated_by="test@example.com",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7),  # Not expired
    )
    db_session.add(valid_report)
    await db_session.commit()
    
    # Run cleanup
    response = await client.post(
        "/api/v1/reports/cleanup",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "deleted_reports" in data
    assert "message" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_report_pagination(
    client: AsyncClient, auth_headers: dict, test_tenant: TenantClient, db_session
):
    """Test pagination for report listing"""
    # Create an analysis
    analysis = Analysis(
        id=uuid4(),
        tenant_client_id=test_tenant.id,
        status="COMPLETED",
        analysis_date=datetime.utcnow(),
        summary={"total_users": 100, "potential_savings": 5000.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(analysis)
    await db_session.commit()
    
    # Generate multiple reports (more than default limit)
    for i in range(3):
        await client.post(
            f"/api/v1/reports/analyses/{analysis.id}/pdf",
            headers=auth_headers,
        )
    
    # Test pagination with limit=2
    response = await client.get(
        f"/api/v1/reports/analyses/{analysis.id}?limit=2&offset=0",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["reports"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["total"] >= 3
    
    # Test second page
    response = await client.get(
        f"/api/v1/reports/analyses/{analysis.id}?limit=2&offset=2",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["reports"]) >= 1  # At least one more report
    assert data["offset"] == 2