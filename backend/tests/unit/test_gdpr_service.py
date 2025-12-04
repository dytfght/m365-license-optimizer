"""
Unit tests for GdprService (LOT 10)
Tests consent management, data export, and right to erasure.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.services.gdpr_service import GdprService


class TestGdprService:
    """Tests for GdprService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.delete = AsyncMock()
        db.add = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create a GdprService instance."""
        return GdprService(mock_db)

    # ============================================
    # Consent Management Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_record_consent_success(self, service, mock_db):
        """Test successful consent recording."""
        tenant_id = uuid4()
        mock_tenant = MagicMock()
        mock_tenant.id = tenant_id
        mock_tenant.gdpr_consent = False
        mock_tenant.gdpr_consent_date = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        mock_db.execute.return_value = mock_result

        result = await service.record_consent(tenant_id, consent_given=True)

        assert result.gdpr_consent is True
        assert result.gdpr_consent_date is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_consent_tenant_not_found(self, service, mock_db):
        """Test consent recording when tenant not found."""
        tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await service.record_consent(tenant_id)

    @pytest.mark.asyncio
    async def test_revoke_consent(self, service, mock_db):
        """Test consent revocation."""
        tenant_id = uuid4()
        mock_tenant = MagicMock()
        mock_tenant.id = tenant_id
        mock_tenant.gdpr_consent = True
        mock_tenant.gdpr_consent_date = datetime.utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_tenant
        mock_db.execute.return_value = mock_result

        result = await service.revoke_consent(tenant_id)

        assert result.gdpr_consent is False
        assert result.gdpr_consent_date is None

    @pytest.mark.asyncio
    async def test_check_consent_true(self, service, mock_db):
        """Test consent check when consent given."""
        tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = True
        mock_db.execute.return_value = mock_result

        result = await service.check_consent(tenant_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_consent_false(self, service, mock_db):
        """Test consent check when consent not given."""
        tenant_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = False
        mock_db.execute.return_value = mock_result

        result = await service.check_consent(tenant_id)

        assert result is False

    # ============================================
    # Data Export Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_export_user_data_success(self, service, mock_db):
        """Test successful user data export."""
        user_id = uuid4()
        
        # Mock user
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.graph_id = "graph-123"
        mock_user.user_principal_name = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.department = "IT"
        mock_user.job_title = "Developer"
        mock_user.office_location = "HQ"
        mock_user.account_enabled = True
        mock_user.member_of_groups = ["Group1"]
        mock_user.created_at = datetime.utcnow()
        mock_user.updated_at = datetime.utcnow()

        # Setup mock returns for different queries
        call_count = 0
        def mock_execute(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:  # User query
                result.scalar_one_or_none.return_value = mock_user
            else:  # License, usage, recommendations queries
                result.scalars.return_value.all.return_value = []
            call_count += 1
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result = await service.export_user_data(user_id)

        assert result["export_type"] == "GDPR_ARTICLE_20_DATA_PORTABILITY"
        assert result["user"]["id"] == str(user_id)
        assert result["user"]["user_principal_name"] == "test@example.com"
        assert "license_assignments" in result
        assert "usage_metrics" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_export_user_data_not_found(self, service, mock_db):
        """Test user data export when user not found."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await service.export_user_data(user_id)

    # ============================================
    # Data Deletion Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_delete_user_data_full_delete(self, service, mock_db):
        """Test full user data deletion."""
        user_id = uuid4()
        
        mock_user = MagicMock()
        mock_user.id = user_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await service.delete_user_data(user_id, anonymize=False)

        assert result["action"] == "deleted"
        assert result["user_id"] == str(user_id)
        mock_db.delete.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_delete_user_data_anonymize(self, service, mock_db):
        """Test user data anonymization."""
        user_id = uuid4()
        
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.user_principal_name = "test@example.com"
        mock_user.display_name = "Test User"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await service.delete_user_data(user_id, anonymize=True)

        assert result["action"] == "anonymized"
        assert mock_user.display_name == "Anonymized User"
        assert "anonymized_" in mock_user.user_principal_name

    @pytest.mark.asyncio
    async def test_delete_user_data_not_found(self, service, mock_db):
        """Test user deletion when user not found."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await service.delete_user_data(user_id)

    # ============================================
    # Registry PDF Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_generate_registry_pdf(self, service):
        """Test GDPR registry PDF generation."""
        pdf_content = await service.generate_registry_pdf()

        assert pdf_content is not None
        assert len(pdf_content) > 0
        # PDF magic bytes
        assert pdf_content[:4] == b"%PDF"
