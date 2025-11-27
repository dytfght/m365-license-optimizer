"""
Unit tests for AnalysisService
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from src.models.analysis import Analysis, AnalysisStatus
from src.models.user import User
from src.models.usage_metrics import UsageMetrics
from src.services.analysis_service import AnalysisService


@pytest.mark.asyncio
async def test_calculate_usage_scores_empty(db_session):
    """Test usage score calculation with empty metrics"""
    service = AnalysisService(db_session)
    
    scores = service._calculate_usage_scores([])
    
    assert scores["Exchange"] == 0.0
    assert scores["OneDrive"] == 0.0
    assert scores["SharePoint"] == 0.0
    assert scores["Teams"] == 0.0
    assert scores["Office"] == 0.0


@pytest.mark.asyncio
async def test_calculate_usage_scores_with_activity(db_session):
    """Test usage score calculation with activity data"""
    service = AnalysisService(db_session)
    
    # Create mock usage metrics
    metrics = [
        UsageMetrics(
            id=uuid4(),
            user_id=uuid4(),
            period="D28",
            report_date=datetime.utcnow().date(),
            email_activity={"send_count": 50, "receive_count": 50},
            onedrive_activity={"viewed_or_edited_file_count": 25},
            sharepoint_activity={"viewed_or_edited_file_count": 25},
            teams_activity={"team_chat_message_count": 50, "meeting_count": 5},
            office_web_activity={"viewed_or_edited_file_count": 15},
            office_desktop_activated=True,
            storage_used_bytes=1024 * 1024,
            mailbox_size_bytes=1024 * 1024,
        )
    ]
    
    scores = service._calculate_usage_scores(metrics)
    
    assert scores["Exchange"] == 1.0  # 100 emails / 100
    assert scores["OneDrive"] == 0.5  # 25 files / 50
    assert scores["SharePoint"] == 0.5  # 25 files / 50
    assert scores["Teams"] == 1.0  # (50 + 5*10) / 100
    assert scores["Office"] == 0.5  # 15 files / 30


@pytest.mark.asyncio
async def test_generate_recommendation_inactive_user(db_session):
    """Test recommendation for inactive user"""
    service = AnalysisService(db_session)
    
    user = User(
        id=uuid4(),
        graph_id="test-user",
        tenant_client_id=uuid4(),
        user_principal_name="inactive@test.com",
        account_enabled=False,
    )
    
    usage_scores = {
        "Exchange": 0.0,
        "OneDrive": 0.0,
        "SharePoint": 0.0,
        "Teams": 0.0,
        "Office": 0.0,
    }
    
    current_sku = "06ebc4ee-1bb5-47dd-8120-11324bc54e06"  # E5
    current_cost = Decimal("10.00")
    
    recommendation = await service._generate_recommendation(
        user, usage_scores, current_sku, current_cost
    )
    
    assert recommendation is not None
    assert recommendation["type"] == "remove"
    assert recommendation["recommended_sku"] is None
    assert recommendation["savings_monthly"] == current_cost
    assert "disabled" in recommendation["reason"].lower()


@pytest.mark.asyncio
async def test_generate_recommendation_low_usage(db_session):
    """Test recommendation for user with very low usage"""
    service = AnalysisService(db_session)
    
    user = User(
        id=uuid4(),
        graph_id="test-user",
        tenant_client_id=uuid4(),
        user_principal_name="lowusage@test.com",
        account_enabled=True,
    )
    
    # Very low usage across all services
    usage_scores = {
        "Exchange": 0.02,
        "OneDrive": 0.01,
        "SharePoint": 0.01,
        "Teams": 0.01,
        "Office": 0.0,
    }
    
    current_sku = "05e9a617-0261-4cee-bb44-138d3ef5d965"  # E3
    current_cost = Decimal("10.00")
    
    recommendation = await service._generate_recommendation(
        user, usage_scores, current_sku, current_cost
    )
    
    assert recommendation is not None
    assert recommendation["type"] == "remove"
    assert "inactive" in recommendation["reason"].lower()


@pytest.mark.asyncio
async def test_generate_recommendation_downgrade_e5_to_e3(db_session):
    """Test recommendation to downgrade from E5 to E3"""
    service = AnalysisService(db_session)
    
    user = User(
        id=uuid4(),
        graph_id="test-user",
        tenant_client_id=uuid4(),
        user_principal_name="user@test.com",
        account_enabled=True,
    )
    
    # Good usage but no advanced features
    usage_scores = {
        "Exchange": 0.8,
        "OneDrive": 0.6,
        "SharePoint": 0.5,
        "Teams": 0.7,
        "Office": 0.6,
    }
    
    current_sku = "06ebc4ee-1bb5-47dd-8120-11324bc54e06"  # E5
    current_cost = Decimal("20.00")
    
    recommendation = await service._generate_recommendation(
        user, usage_scores, current_sku, current_cost
    )
    
    assert recommendation is not None
    assert recommendation["type"] == "downgrade"
    assert recommendation["recommended_sku"] == "05e9a617-0261-4cee-bb44-138d3ef5d965"  # E3
    assert recommendation["savings_monthly"] > 0
    assert "advanced" in recommendation["reason"].lower()


@pytest.mark.asyncio
async def test_generate_recommendation_downgrade_e3_to_e1(db_session):
    """Test recommendation to downgrade from E3 to E1"""
    service = AnalysisService(db_session)
    
    user = User(
        id=uuid4(),
        graph_id="test-user",
        tenant_client_id=uuid4(),
        user_principal_name="user@test.com",
        account_enabled=True,
    )
    
    # Good usage but no Office desktop
    usage_scores = {
        "Exchange": 0.8,
        "OneDrive": 0.6,
        "SharePoint": 0.5,
        "Teams": 0.7,
        "Office": 0.0,  # No Office usage
    }
    
    current_sku = "05e9a617-0261-4cee-bb44-138d3ef5d965"  # E3
    current_cost = Decimal("15.00")
    
    recommendation = await service._generate_recommendation(
        user, usage_scores, current_sku, current_cost
    )
    
    assert recommendation is not None
    assert recommendation["type"] == "downgrade"
    assert recommendation["recommended_sku"] == "18181a46-0d4e-45cd-891e-60aabd171b4e"  # E1
    assert recommendation["savings_monthly"] > 0
    assert "office" in recommendation["reason"].lower()


@pytest.mark.asyncio
async def test_generate_recommendation_no_change(db_session):
    """Test no recommendation when usage matches SKU"""
    service = AnalysisService(db_session)
    
    user = User(
        id=uuid4(),
        graph_id="test-user",
        tenant_client_id=uuid4(),
        user_principal_name="user@test.com",
        account_enabled=True,
    )
    
    # Good usage matching E1
    usage_scores = {
        "Exchange": 0.8,
        "OneDrive": 0.6,
        "SharePoint": 0.5,
        "Teams": 0.7,
        "Office": 0.0,
    }
    
    current_sku = "18181a46-0d4e-45cd-891e-60aabd171b4e"  # E1
    current_cost = Decimal("8.00")
    
    recommendation = await service._generate_recommendation(
        user, usage_scores, current_sku, current_cost
    )
    
    # No recommendation (usage matches SKU)
    assert recommendation is None


@pytest.mark.asyncio
async def test_generate_recommendation_no_license(db_session):
    """Test no recommendation when user has no license"""
    service = AnalysisService(db_session)
    
    user = User(
        id=uuid4(),
        graph_id="test-user",
        tenant_client_id=uuid4(),
        user_principal_name="user@test.com",
        account_enabled=True,
    )
    
    usage_scores = {
        "Exchange": 0.0,
        "OneDrive": 0.0,
        "SharePoint": 0.0,
        "Teams": 0.0,
        "Office": 0.0,
    }
    
    recommendation = await service._generate_recommendation(
        user, usage_scores, None, Decimal("0.00")
    )
    
    assert recommendation is None
