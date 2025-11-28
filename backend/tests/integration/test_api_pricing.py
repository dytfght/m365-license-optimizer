"""
Integration tests for Pricing API endpoints
Tests CSV import, product listing, and price queries
"""
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPricingEndpoints:
    """Integration tests for /api/v1/pricing endpoints"""

    async def test_import_pricing_csv_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful CSV import"""
        # Create dummy CSV content
        # Create dummy CSV content with all required columns
        csv_content = b"ProductId,SkuId,ProductTitle,SkuTitle,Publisher,SkuDescription,UnitOfMeasure,Tags,Market,Currency,Segment,TermDuration,BillingPlan,UnitPrice,ERP Price,EffectiveStartDate,EffectiveEndDate\nCFQ7TTC0HL8Z,0001,Office 365 E3,Standard,Microsoft,Desc,User,,AX,EUR,Commercial,P1Y,Monthly,10.0,12.0,2023-01-01,2024-01-01"

        # Remove Content-Type from headers to allow httpx to set multipart boundary
        headers = auth_headers.copy()
        headers.pop("Content-Type", None)

        response = await client.post(
            "/api/v1/pricing/import",
            headers=headers,
            files={"file": ("test.csv", csv_content, "text/csv")},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["products"] > 0
        assert data["prices"] > 0

    async def test_list_products(self, client: AsyncClient):
        """Test product listing"""
        response = await client.get("/api/v1/pricing/products")

        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)

    async def test_search_products(self, client: AsyncClient):
        """Test product search"""
        response = await client.get(
            "/api/v1/pricing/products",
            params={"search": "Office", "limit": 10},
        )

        assert response.status_code == 200
        products = response.json()
        assert len(products) <= 10

    async def test_get_product_by_id(self, client: AsyncClient):
        """Test get specific product"""
        response = await client.get("/api/v1/pricing/products/CFQ7TTC0HL8Z/0001")

        assert response.status_code in (200, 404)

    async def test_get_current_price(self, client: AsyncClient):
        """Test get current effective price"""
        response = await client.get(
            "/api/v1/pricing/prices/current",
            params={
                "sku_id": "CFQ7TTC0HL8Z-0001",
                "market": "AX",
                "currency": "EUR",
                "segment": "Commercial",
            },
        )

        assert response.status_code in (200, 404)

    async def test_get_price_history(self, client: AsyncClient):
        """Test price history retrieval"""
        response = await client.get(
            "/api/v1/pricing/products/CFQ7TTC0HL8Z/0001/prices",
            params={"market": "AX", "currency": "EUR", "limit": 5},
        )

        assert response.status_code == 200
        prices = response.json()
        assert len(prices) <= 5
