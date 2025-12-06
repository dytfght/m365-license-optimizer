"""
Unit tests for Add-on Validator Service
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.models.addon_compatibility import AddonCompatibility


class TestAddonValidator:
    """Test suite for AddonValidator"""

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = AsyncMock()
        # Configure execute to return a MagicMock (not AsyncMock) for the result
        # This ensures result.scalars() is synchronous and returns a mock that has .all()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result
        return session

    @pytest.fixture
    def mock_addon_repo(self):
        """Mock addon repository"""
        repo = AsyncMock()
        repo.get_specific_mapping = AsyncMock(return_value=None)
        repo.get_by_service_type = AsyncMock(return_value=[])
        repo.get_by_addon_sku = AsyncMock(return_value=[])
        repo.get_by_base_sku = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def validator(self, mock_session, mock_addon_repo):
        """Addon validator instance"""
        from src.services.addon_validator import AddonValidator

        # Créer le validator avec le vrai repository mais avec notre mock session
        validator = AddonValidator(mock_session)
        # Remplacer le repo par notre mock
        validator.addon_repo = mock_addon_repo
        return validator

    @pytest.fixture
    def mock_compatibility_mapping(self):
        """Mock add-on compatibility mapping"""
        mapping = MagicMock(spec=AddonCompatibility)
        mapping.id = uuid4()
        mapping.addon_sku_id = "0001"
        mapping.addon_product_id = "CFQ7TTC0P0HP"
        mapping.base_sku_id = "0001"
        mapping.base_product_id = "CFQ7TTC0LF8S"
        mapping.service_type = "Microsoft 365"
        mapping.addon_category = "Audio Conferencing"
        mapping.min_quantity = 1
        mapping.max_quantity = None
        mapping.quantity_multiplier = 1
        mapping.requires_domain_validation = False
        mapping.requires_tenant_validation = False
        mapping.is_active = True
        mapping.is_available.return_value = True
        mapping.validation_metadata = None
        mapping.effective_date = None
        mapping.expiration_date = None
        return mapping

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_success(
        self, validator, mock_compatibility_mapping
    ):
        """Test successful add-on compatibility validation"""
        validator.addon_repo.get_specific_mapping.return_value = (
            mock_compatibility_mapping
        )
        # Mock the async methods that are called internally
        validator._validate_business_rules = AsyncMock(return_value=(True, []))
        validator._validate_service_limits = AsyncMock(return_value=(True, []))

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 5, "12345678-1234-1234-1234-123456789012", "contoso.com"
        )

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_no_mapping(self, validator):
        """Test validation when no compatibility mapping exists"""
        validator.addon_repo.get_specific_mapping = AsyncMock(return_value=None)

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1
        )

        assert is_valid is False
        assert len(errors) == 1
        assert "No compatibility mapping found" in errors[0]

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_inactive_mapping(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with inactive mapping"""
        mock_compatibility_mapping.is_active = False
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1
        )

        assert is_valid is False
        assert len(errors) == 2  # inactive + not available
        assert any("inactive" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_unavailable_mapping(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with unavailable mapping (expired)"""
        mock_compatibility_mapping.is_available.return_value = False
        mock_compatibility_mapping.expiration_date = datetime.utcnow() - timedelta(
            days=1
        )
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )
        # Mock the async methods
        validator._validate_business_rules = AsyncMock(return_value=(True, []))
        validator._validate_service_limits = AsyncMock(return_value=(True, []))

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1
        )

        assert is_valid is False
        assert len(errors) == 1
        assert "not currently available" in errors[0]

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_quantity_too_low(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with quantity below minimum"""
        mock_compatibility_mapping.min_quantity = 5
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1
        )

        assert is_valid is False
        assert any("below minimum" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_quantity_too_high(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with quantity above maximum"""
        mock_compatibility_mapping.max_quantity = 10
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 15
        )

        assert is_valid is False
        assert any("exceeds maximum" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_quantity_multiplier(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with quantity not matching multiplier"""
        mock_compatibility_mapping.quantity_multiplier = 5
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 3
        )

        assert is_valid is False
        assert any("multiple of" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_invalid_quantity(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with invalid quantity"""
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        # Test zero quantity
        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 0
        )
        assert is_valid is False
        assert any("greater than 0" in error for error in errors)

        # Test excessive quantity
        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 15000
        )
        assert is_valid is False
        assert any("exceeds reasonable maximum" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_tenant_validation_required(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation when tenant validation is required but not provided"""
        mock_compatibility_mapping.requires_tenant_validation = True
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1
        )

        assert is_valid is False
        assert any("Tenant ID is required" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_domain_validation_required(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation when domain validation is required but not provided"""
        mock_compatibility_mapping.requires_domain_validation = True
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1
        )

        assert is_valid is False
        assert any("Domain name is required" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_invalid_tenant_id(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with invalid tenant ID format"""
        mock_compatibility_mapping.requires_tenant_validation = True
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1, tenant_id="invalid-tenant-format"
        )

        assert is_valid is False
        assert any("Invalid tenant ID format" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_invalid_domain_name(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with invalid domain name format"""
        mock_compatibility_mapping.requires_domain_validation = True
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001", "0001", 1, domain_name="invalid domain!"
        )

        assert is_valid is False
        assert any("Invalid domain name format" in error for error in errors)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_valid_tenant_and_domain(
        self, validator, mock_compatibility_mapping
    ):
        """Test validation with valid tenant ID and domain name"""
        mock_compatibility_mapping.requires_tenant_validation = True
        mock_compatibility_mapping.requires_domain_validation = True
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )
        # Mock the async internal validation methods
        validator._validate_business_rules = AsyncMock(return_value=(True, []))
        validator._validate_service_limits = AsyncMock(return_value=(True, []))

        is_valid, errors = await validator.validate_addon_compatibility(
            "0001",
            "0001",
            1,
            tenant_id="12345678-1234-1234-1234-123456789012",
            domain_name="contoso.com",
        )

        assert is_valid is True
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_is_valid_tenant_id(self, validator):
        """Test tenant ID format validation"""
        # Valid tenant IDs
        assert validator._is_valid_tenant_id("12345678-1234-1234-1234-123456789012")
        assert validator._is_valid_tenant_id("AAAAAAAA-1234-1234-1234-123456789012")

        # Invalid tenant IDs
        assert not validator._is_valid_tenant_id("invalid-tenant")
        assert not validator._is_valid_tenant_id("12345678-1234-1234-1234")
        assert not validator._is_valid_tenant_id("")

    @pytest.mark.asyncio
    async def test_is_valid_domain_name(self, validator):
        """Test domain name format validation"""
        # Valid domain names
        assert validator._is_valid_domain_name("contoso.com")
        assert validator._is_valid_domain_name("subdomain.contoso.com")
        assert validator._is_valid_domain_name("contoso.co.uk")

        # Invalid domain names
        assert not validator._is_valid_domain_name("invalid domain!")
        assert not validator._is_valid_domain_name("-contoso.com")
        assert not validator._is_valid_domain_name("contoso-.com")
        assert not validator._is_valid_domain_name("")

    @pytest.mark.asyncio
    async def test_validate_bulk_addons_success(
        self, validator, mock_compatibility_mapping
    ):
        """Test bulk validation of multiple add-ons"""
        # Mock repository to return valid mapping for both requests
        validator.addon_repo.get_specific_mapping.return_value = mock_compatibility_mapping
        # Mock the async internal validation methods
        validator._validate_business_rules = AsyncMock(return_value=(True, []))
        validator._validate_service_limits = AsyncMock(return_value=(True, []))

        addons = [
            {"sku_id": "0001", "quantity": 1},
            {"sku_id": "0002", "quantity": 2},
        ]

        all_valid, results = await validator.validate_bulk_addons(
            addons, "0001", "12345678-1234-1234-1234-123456789012", "contoso.com"
        )

        assert all_valid is True
        assert len(results) == 0  # No errors means empty dict

    @pytest.mark.asyncio
    async def test_validate_bulk_addons_with_errors(
        self, validator, mock_compatibility_mapping
    ):
        """Test bulk validation with some invalid add-ons"""
        # First call returns valid mapping, second call returns None (invalid)
        validator.addon_repo.get_specific_mapping = AsyncMock(
            side_effect=[mock_compatibility_mapping, None]
        )
        # Mock async methods for the valid one
        validator._validate_business_rules = AsyncMock(return_value=(True, []))
        validator._validate_service_limits = AsyncMock(return_value=(True, []))

        addons = [
            {"sku_id": "0001", "quantity": 1},
            {"sku_id": "0002", "quantity": 2},  # This will fail
        ]

        all_valid, results = await validator.validate_bulk_addons(addons, "0001")

        assert all_valid is False
        assert len(results) == 1  # Only the invalid one should have errors
        assert "0002" in results
        assert len(results["0002"]) > 0

    @pytest.mark.asyncio
    async def test_get_validation_requirements(
        self, validator, mock_compatibility_mapping
    ):
        """Test getting validation requirements for an add-on"""
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        requirements = await validator.get_validation_requirements("0001", "0001")

        assert requirements["requires_validation"] is True
        assert requirements["min_quantity"] == 1
        assert requirements["max_quantity"] is None
        assert requirements["quantity_multiplier"] == 1
        assert requirements["requires_tenant_validation"] is False
        assert requirements["requires_domain_validation"] is False
        assert requirements["service_type"] == "Microsoft 365"
        assert requirements["addon_category"] == "Audio Conferencing"
        assert requirements["is_active"] is True
        assert requirements["is_available"] is True
        assert "validation_rules" in requirements

    @pytest.mark.asyncio
    async def test_get_validation_requirements_no_mapping(self, validator):
        """Test getting validation requirements when no mapping exists"""
        validator.addon_repo.get_specific_mapping = AsyncMock(return_value=None)

        requirements = await validator.get_validation_requirements("0001", "0001")

        assert requirements["requires_validation"] is False
        assert "No compatibility mapping found" in requirements["reason"]

    @pytest.mark.asyncio
    async def test_get_sku_validation_summary(
        self, validator, mock_compatibility_mapping
    ):
        """Test getting validation summary for all add-ons compatible with a SKU"""
        validator.addon_repo.get_compatible_addons = AsyncMock(
            return_value=[mock_compatibility_mapping]
        )
        validator.addon_repo.get_specific_mapping = AsyncMock(
            return_value=mock_compatibility_mapping
        )

        summary = await validator.get_sku_validation_summary("0001")

        assert summary["total_compatible_addons"] == 1
        assert summary["active_mappings"] == 1
        assert "validation_requirements" in summary
        assert "service_types" in summary
        assert "addon_categories" in summary
        assert "Microsoft 365" in summary["service_types"]
        assert "Audio Conferencing" in summary["addon_categories"]

    @pytest.mark.asyncio
    async def test_get_sku_validation_summary_no_addons(self, validator):
        """Test getting validation summary when no compatible add-ons exist"""
        validator.addon_repo.get_compatible_addons = AsyncMock(return_value=[])

        summary = await validator.get_sku_validation_summary("0001")

        assert summary["total_compatible_addons"] == 0
        assert summary["active_mappings"] == 0
        assert len(summary["service_types"]) == 0
        assert len(summary["addon_categories"]) == 0
