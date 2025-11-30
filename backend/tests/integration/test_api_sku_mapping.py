"""
Integration tests for SKU Mapping API endpoints
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.addon_compatibility import AddonCompatibility
from src.models.microsoft_product import MicrosoftProduct
from src.models.user import User


class TestSkuMappingAPI:
    """Test suite for SKU Mapping API endpoints"""

    @pytest.fixture
    async def admin_user(self, db_session: AsyncSession) -> User:
        """Create admin user for testing"""
        from src.models.tenant import TenantClient

        # Create a tenant first
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Tenant",
            country="FR",
            default_language="fr",
            onboarding_status="active",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid4(),
            graph_id=str(uuid4()),
            user_principal_name="admin@test.com",
            display_name="Test Admin",
            account_enabled=True,
            tenant_client_id=tenant.id,
        )
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.fixture
    async def auth_headers(self, admin_user: User, client: AsyncClient) -> dict:
        """Get authentication headers for admin user"""
        # Mock authentication - in real tests, you'd get a proper token
        return {"Authorization": f"Bearer test-token-{admin_user.id}"}

    @pytest.fixture
    async def sample_products(self, db_session: AsyncSession) -> list:
        """Create sample Microsoft products for testing"""
        products = [
            MicrosoftProduct(
                product_id="CFQ7TTC0LF8S",
                sku_id="0001",
                product_title="Microsoft 365 Business",
                sku_title="Microsoft 365 Business Premium",
                publisher="Microsoft Corporation",
            ),
            MicrosoftProduct(
                product_id="CFQ7TTC0P0HP",
                sku_id="0001",
                product_title="Microsoft 365 Audio Conferencing",
                sku_title="Microsoft 365 Audio Conferencing",
                publisher="Microsoft Corporation",
            ),
        ]

        for product in products:
            # Vérifier si le produit existe déjà
            existing = await db_session.execute(
                select(MicrosoftProduct).where(
                    MicrosoftProduct.product_id == product.product_id,
                    MicrosoftProduct.sku_id == product.sku_id,
                )
            )
            if not existing.scalar_one_or_none():
                db_session.add(product)
        await db_session.commit()
        return products

    @pytest.fixture
    async def sample_compatibility_mapping(
        self, db_session: AsyncSession, sample_products: list
    ) -> AddonCompatibility:
        """Create sample compatibility mapping for testing"""
        mapping = AddonCompatibility(
            addon_sku_id="0001",
            addon_product_id="CFQ7TTC0P0HP",
            base_sku_id="0001",
            base_product_id="CFQ7TTC0LF8S",
            service_type="Microsoft 365",
            addon_category="Audio Conferencing",
            min_quantity=1,
            max_quantity=None,
            quantity_multiplier=1,
            requires_domain_validation=False,
            requires_tenant_validation=False,
            is_active=True,
            description="Audio Conferencing for Microsoft 365 Business Premium",
        )
        db_session.add(mapping)
        await db_session.commit()
        return mapping

    @pytest.mark.asyncio
    async def test_get_sku_mapping_summary(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting SKU mapping summary"""
        response = await client.get(
            "/api/v1/admin/sku-mapping/summary", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_partner_center_products" in data
        assert "total_compatibility_mappings" in data
        assert "active_mappings" in data
        assert "service_type_distribution" in data
        assert "addon_category_distribution" in data
        assert "mapping_coverage" in data

    @pytest.mark.asyncio
    async def test_sync_partner_center_products(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test syncing Partner Center products"""
        response = await client.post(
            "/api/v1/admin/sku-mapping/sync/products",
            headers=auth_headers,
            params={"country": "US", "currency": "USD"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "created" in data
        assert "updated" in data
        assert isinstance(data["created"], int)
        assert isinstance(data["updated"], int)

    @pytest.mark.asyncio
    async def test_sync_addon_compatibility_rules(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test syncing add-on compatibility rules"""
        response = await client.post(
            "/api/v1/admin/sku-mapping/sync/compatibility", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "created" in data
        assert "updated" in data
        assert isinstance(data["created"], int)
        assert isinstance(data["updated"], int)

    @pytest.mark.asyncio
    async def test_get_compatible_addons(
        self, client: AsyncClient, auth_headers: dict, sample_products: list
    ):
        """Test getting compatible add-ons for a base SKU"""
        response = await client.get(
            f"/api/v1/admin/sku-mapping/compatible-addons/{sample_products[0].sku_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Response might be empty if no mappings exist, but structure should be correct

    @pytest.mark.asyncio
    async def test_get_compatible_addons_with_filters(
        self, client: AsyncClient, auth_headers: dict, sample_products: list
    ):
        """Test getting compatible add-ons with service type and category filters"""
        response = await client.get(
            f"/api/v1/admin/sku-mapping/compatible-addons/{sample_products[0].sku_id}",
            headers=auth_headers,
            params={
                "service_type": "Microsoft 365",
                "addon_category": "Audio Conferencing",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_compatibility_mapping: AddonCompatibility,
    ):
        """Test successful add-on compatibility validation"""
        response = await client.post(
            "/api/v1/admin/sku-mapping/validate-addon",
            headers=auth_headers,
            json={
                "addon_sku_id": sample_compatibility_mapping.addon_sku_id,
                "base_sku_id": sample_compatibility_mapping.base_sku_id,
                "quantity": 5,
                "tenant_id": "12345678-1234-1234-1234-123456789012",
                "domain_name": "contoso.com",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is True
        assert len(data["errors"]) == 0
        assert data["addon_sku_id"] == sample_compatibility_mapping.addon_sku_id
        assert data["base_sku_id"] == sample_compatibility_mapping.base_sku_id
        assert data["quantity"] == 5

    @pytest.mark.asyncio
    async def test_validate_addon_compatibility_failure(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test failed add-on compatibility validation"""
        response = await client.post(
            "/api/v1/admin/sku-mapping/validate-addon",
            headers=auth_headers,
            json={
                "addon_sku_id": "nonexistent",
                "base_sku_id": "nonexistent",
                "quantity": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_valid"] is False
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_list_compatibility_mappings(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_compatibility_mapping: AddonCompatibility,
    ):
        """Test listing compatibility mappings"""
        response = await client.get(
            "/api/v1/admin/sku-mapping/compatibility-mappings", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1

        # Check first mapping structure
        mapping = data[0]
        assert "id" in mapping
        assert "addon_sku_id" in mapping
        assert "base_sku_id" in mapping
        assert "service_type" in mapping
        assert "addon_category" in mapping
        assert "is_active" in mapping

    @pytest.mark.asyncio
    async def test_list_compatibility_mappings_with_filters(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_compatibility_mapping: AddonCompatibility,
    ):
        """Test listing compatibility mappings with filters"""
        response = await client.get(
            "/api/v1/admin/sku-mapping/compatibility-mappings",
            headers=auth_headers,
            params={
                "service_type": "Microsoft 365",
                "addon_category": "Audio Conferencing",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should return mappings matching the filters

    @pytest.mark.asyncio
    async def test_create_compatibility_mapping(
        self, client: AsyncClient, auth_headers: dict, sample_products: list
    ):
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
            "requires_domain_validation": False,
            "requires_tenant_validation": False,
            "is_active": True,
            "description": "Test mapping",
        }

        response = await client.post(
            "/api/v1/admin/sku-mapping/compatibility-mappings",
            headers=auth_headers,
            json=mapping_data,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["addon_sku_id"] == mapping_data["addon_sku_id"]
        assert data["base_sku_id"] == mapping_data["base_sku_id"]
        assert data["service_type"] == mapping_data["service_type"]
        assert data["addon_category"] == mapping_data["addon_category"]

    @pytest.mark.asyncio
    async def test_update_compatibility_mapping(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_compatibility_mapping: AddonCompatibility,
    ):
        """Test updating an existing compatibility mapping"""
        update_data = {
            "description": "Updated description",
            "min_quantity": 2,
            "is_active": False,
        }

        response = await client.put(
            f"/api/v1/admin/sku-mapping/compatibility-mappings/{sample_compatibility_mapping.id}",
            headers=auth_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["description"] == update_data["description"]
        assert data["min_quantity"] == update_data["min_quantity"]
        assert data["is_active"] == update_data["is_active"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_mapping(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating a non-existent compatibility mapping"""
        fake_id = "12345678-1234-1234-1234-123456789012"

        response = await client.put(
            f"/api/v1/admin/sku-mapping/compatibility-mappings/{fake_id}",
            headers=auth_headers,
            json={"description": "Updated"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_compatibility_mapping(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_compatibility_mapping: AddonCompatibility,
    ):
        """Test deleting a compatibility mapping"""
        response = await client.delete(
            f"/api/v1/admin/sku-mapping/compatibility-mappings/{sample_compatibility_mapping.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Compatibility mapping deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_mapping(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting a non-existent compatibility mapping"""
        fake_id = "12345678-1234-1234-1234-123456789012"

        response = await client.delete(
            f"/api/v1/admin/sku-mapping/compatibility-mappings/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_addon_recommendations(
        self, client: AsyncClient, auth_headers: dict, sample_products: list
    ):
        """Test getting add-on recommendations"""
        response = await client.get(
            f"/api/v1/admin/sku-mapping/recommendations/{sample_products[0].sku_id}",
            headers=auth_headers,
            params={"current_addons": "0002,0003", "tenant_size": "medium"},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Recommendations might be empty, but structure should be correct

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test unauthorized access to admin endpoints"""
        response = await client.get("/api/v1/admin/sku-mapping/summary")

        # Should return 401 or 403 for unauthorized access
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_invalid_validation_request(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test validation with invalid request data"""
        response = await client.post(
            "/api/v1/admin/sku-mapping/validate-addon",
            headers=auth_headers,
            json={
                "addon_sku_id": "",  # Invalid empty SKU
                "base_sku_id": "",
                "quantity": 0,  # Invalid quantity
            },
        )

        # Should handle validation errors gracefully
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_pagination_for_mappings(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test pagination for compatibility mappings list"""
        response = await client.get(
            "/api/v1/admin/sku-mapping/compatibility-mappings",
            headers=auth_headers,
            params={"limit": 5, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 5  # Should respect limit

    @pytest.mark.asyncio
    async def test_filter_by_active_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_compatibility_mapping: AddonCompatibility,
    ):
        """Test filtering compatibility mappings by active status"""
        response = await client.get(
            "/api/v1/admin/sku-mapping/compatibility-mappings",
            headers=auth_headers,
            params={"is_active": True},
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # All returned mappings should be active
        for mapping in data:
            assert mapping["is_active"] is True
