"""
Unit tests for SKU Mapping Service
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.models.addon_compatibility import AddonCompatibility
from src.models.microsoft_product import MicrosoftProduct
from src.services.sku_mapping_service import SkuMappingService


class TestSkuMappingService:
    """Test suite for SkuMappingService"""

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def sku_service(self, mock_session):
        """SKU mapping service instance"""
        return SkuMappingService(mock_session)

    @pytest.fixture
    def mock_product(self):
        """Mock Microsoft product"""
        product = MagicMock(spec=MicrosoftProduct)
        product.id = uuid4()
        product.product_id = "CFQ7TTC0LF8S"
        product.sku_id = "0001"
        product.product_title = "Microsoft 365 Business Premium"
        product.sku_title = "Microsoft 365 Business Premium"
        return product

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
        mapping.is_active = True
        mapping.is_available.return_value = True
        mapping.is_compatible.return_value = True
        return mapping

    @pytest.mark.asyncio
    async def test_get_graph_sku_info(self, sku_service):
        """Test getting Graph API SKU information"""
        result = await sku_service.get_graph_sku_info("O365_BUSINESS_PREMIUM")

        assert result is not None
        assert result["sku_id"] == "O365_BUSINESS_PREMIUM"
        assert result["name"] == "Microsoft 365 Business Premium"
        assert "service_plans" in result
        assert "category" in result

    @pytest.mark.asyncio
    async def test_get_graph_sku_info_not_found(self, sku_service):
        """Test getting non-existent Graph API SKU"""
        result = await sku_service.get_graph_sku_info("NONEXISTENT_SKU")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_partner_center_sku_found(self, sku_service, mock_product):
        """Test getting Partner Center SKU for existing Graph SKU"""
        sku_service.product_repo.get_by_product_sku = AsyncMock(
            return_value=mock_product
        )

        result = await sku_service.get_partner_center_sku("O365_BUSINESS_PREMIUM")

        assert result is not None
        assert result == mock_product
        sku_service.product_repo.get_by_product_sku.assert_called_once_with(
            "CFQ7TTC0LF8S", "0001"
        )

    @pytest.mark.asyncio
    async def test_get_partner_center_sku_not_found(self, sku_service):
        """Test getting Partner Center SKU for non-existent Graph SKU"""
        sku_service.product_repo.get_by_product_and_sku = AsyncMock(return_value=None)

        result = await sku_service.get_partner_center_sku("NONEXISTENT_SKU")

        assert result is None

    @pytest.mark.asyncio
    async def test_map_graph_to_partner_center(self, sku_service, mock_product):
        """Test mapping multiple Graph SKUs to Partner Center"""
        sku_service.product_repo.get_by_product_sku = AsyncMock(
            return_value=mock_product
        )

        graph_skus = ["O365_BUSINESS_PREMIUM", "ENTERPRISEPACK", "NONEXISTENT"]
        result = await sku_service.map_graph_to_partner_center(graph_skus)

        assert len(result) == 3
        assert result["O365_BUSINESS_PREMIUM"] == mock_product
        assert result["ENTERPRISEPACK"] == mock_product
        assert result["NONEXISTENT"] is None

    @pytest.mark.asyncio
    async def test_get_compatible_addons(self, sku_service, mock_compatibility_mapping):
        """Test getting compatible add-ons for a base SKU"""
        sku_service.get_partner_center_sku = AsyncMock(
            return_value=MagicMock(sku_id="0001")
        )
        sku_service.addon_repo.get_compatible_addons = AsyncMock(
            return_value=[mock_compatibility_mapping]
        )
        sku_service.get_graph_sku_info = AsyncMock(
            return_value={
                "sku_id": "AUDIO_CONF",
                "name": "Audio Conferencing",
                "service_plans": ["AUDIO_CONF"],
                "category": "Conferencing",
            }
        )

        result = await sku_service.get_compatible_addons("O365_BUSINESS_PREMIUM")

        assert len(result) == 1
        assert result[0]["sku_id"] == "AUDIO_CONF"
        assert result[0]["name"] == "Audio Conferencing"
        assert "compatibility_rules" in result[0]

    @pytest.mark.asyncio
    async def test_get_compatible_addons_no_partner_mapping(self, sku_service):
        """Test getting compatible add-ons when Partner Center mapping doesn't exist"""
        sku_service.get_partner_center_sku = AsyncMock(return_value=None)

        result = await sku_service.get_compatible_addons("NONEXISTENT_SKU")

        assert result == []

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_success(
        self, sku_service, mock_product
    ):
        """Test successful add-on compatibility validation"""
        sku_service.get_partner_center_sku = AsyncMock(return_value=mock_product)
        sku_service.addon_repo.validate_compatibility = AsyncMock(return_value=True)

        is_valid, error_message = await sku_service.validate_addon_compatibility(
            "AUDIO_CONF", "O365_BUSINESS_PREMIUM", 5
        )

        assert is_valid is True
        assert error_message is None

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_failure(
        self, sku_service, mock_product
    ):
        """Test failed add-on compatibility validation"""
        sku_service.get_partner_center_sku = AsyncMock(return_value=mock_product)
        sku_service.addon_repo.validate_compatibility = AsyncMock(return_value=False)

        is_valid, error_message = await sku_service.validate_addon_compatibility(
            "AUDIO_CONF", "O365_BUSINESS_PREMIUM", 5
        )

        assert is_valid is False
        assert error_message is not None
        assert "not compatible" in error_message

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_no_base_mapping(self, sku_service):
        """Test add-on validation when base SKU has no Partner Center mapping"""
        sku_service.get_partner_center_sku = AsyncMock(return_value=None)

        is_valid, error_message = await sku_service.validate_addon_compatibility(
            "AUDIO_CONF", "NONEXISTENT_BASE", 5
        )

        assert is_valid is False
        assert "not found" in error_message

    @pytest.mark.asyncio
    async def test_create_mapping(self, sku_service):
        """Test creating a new compatibility mapping"""
        mapping_data = {
            "addon_sku_id": "0001",
            "addon_product_id": "CFQ7TTC0P0HP",
            "base_sku_id": "0001",
            "base_product_id": "CFQ7TTC0LF8S",
            "service_type": "Microsoft 365",
            "addon_category": "Audio Conferencing",
            "min_quantity": 1,
            "max_quantity": None,
            "quantity_multiplier": 1,
            "description": "Test mapping",
        }

        mock_mapping = MagicMock(spec=AddonCompatibility)
        mock_mapping.id = uuid4()
        for key, value in mapping_data.items():
            setattr(mock_mapping, key, value)

        sku_service.addon_repo.create = AsyncMock(return_value=mock_mapping)

        result = await sku_service.create_mapping(**mapping_data)

        assert result == mock_mapping
        sku_service.addon_repo.create.assert_called_once_with(**mapping_data)

    @pytest.mark.asyncio
    async def test_update_mapping_success(self, sku_service):
        """Test updating an existing mapping"""
        mapping_id = uuid4()
        update_data = {"description": "Updated description", "min_quantity": 2}

        mock_mapping = MagicMock(spec=AddonCompatibility)
        mock_mapping.id = mapping_id

        sku_service.addon_repo.get_by_id = AsyncMock(return_value=mock_mapping)
        sku_service.addon_repo.update = AsyncMock(return_value=mock_mapping)

        result = await sku_service.update_mapping(mapping_id, **update_data)

        assert result == mock_mapping
        sku_service.addon_repo.update.assert_called_once_with(
            mock_mapping, **update_data
        )

    @pytest.mark.asyncio
    async def test_update_mapping_not_found(self, sku_service):
        """Test updating a non-existent mapping"""
        mapping_id = uuid4()
        update_data = {"description": "Updated description"}

        sku_service.addon_repo.get_by_id = AsyncMock(return_value=None)

        result = await sku_service.update_mapping(mapping_id, **update_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_mapping_success(self, sku_service):
        """Test deleting an existing mapping"""
        mapping_id = uuid4()
        mock_mapping = MagicMock(spec=AddonCompatibility)
        mock_mapping.id = mapping_id

        sku_service.addon_repo.get_by_id = AsyncMock(return_value=mock_mapping)
        sku_service.addon_repo.delete = AsyncMock()

        success = await sku_service.delete_mapping(mapping_id)

        assert success is True
        sku_service.addon_repo.delete.assert_called_once_with(mock_mapping)

    @pytest.mark.asyncio
    async def test_delete_mapping_not_found(self, sku_service):
        """Test deleting a non-existent mapping"""
        mapping_id = uuid4()

        sku_service.addon_repo.get_by_id = AsyncMock(return_value=None)

        success = await sku_service.delete_mapping(mapping_id)

        assert success is False

    @pytest.mark.asyncio
    async def test_get_sku_mapping_summary(
        self, sku_service, mock_product, mock_compatibility_mapping
    ):
        """Test getting SKU mapping summary"""
        sku_service.product_repo.get_all = AsyncMock(return_value=[mock_product] * 10)
        sku_service.addon_repo.get_all = AsyncMock(
            return_value=[mock_compatibility_mapping] * 20
        )

        result = await sku_service.get_sku_mapping_summary()

        assert result["total_partner_center_products"] == 10
        assert result["total_compatibility_mappings"] == 20
        assert "service_type_distribution" in result
        assert "addon_category_distribution" in result
        assert "mapping_coverage" in result

    @pytest.mark.asyncio
    async def test_get_sku_mapping_summary_empty(self, sku_service):
        """Test getting SKU mapping summary with empty data"""
        sku_service.product_repo.get_all = AsyncMock(return_value=[])
        sku_service.addon_repo.get_all = AsyncMock(return_value=[])

        result = await sku_service.get_sku_mapping_summary()

        assert result["total_partner_center_products"] == 0
        assert result["total_compatibility_mappings"] == 0
        assert result["mapping_coverage"] == 0
