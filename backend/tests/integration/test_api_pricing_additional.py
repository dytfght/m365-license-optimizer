"""
Additional integration tests for pricing API
Tests authentication, error handling, and edge cases
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPricingAPIAdditional:
    """Additional integration tests for pricing endpoints"""

    async def test_import_csv_without_auth(self, client: AsyncClient):
        """Test CSV import requires authentication"""
        response = await client.post(
            "/api/v1/pricing/import",
            files={"file": ("test.csv", b"test,data", "text/csv")},
        )
        assert response.status_code == 401

    async def test_import_csv_invalid_file_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test CSV import rejects non-CSV files"""
        # Remove Content-Type from headers to allow httpx to set multipart boundary
        headers = auth_headers.copy()
        headers.pop("Content-Type", None)

        response = await client.post(
            "/api/v1/pricing/import",
            headers=headers,
            files={"file": ("test.txt", b"test data", "text/plain")},
        )
        assert response.status_code == 400

    async def test_get_product_pagination(self, client: AsyncClient):
        """Test product listing respects limit parameter"""
        response = await client.get(
            "/api/v1/pricing/products",
            params={"limit": 5},
        )
        assert response.status_code == 200
        products = response.json()
        assert len(products) <= 5

    async def test_get_current_price_missing_params(self, client: AsyncClient):
        """Test current price endpoint validates required params"""
        response = await client.get("/api/v1/pricing/prices/current")
        assert response.status_code == 422  # Validation error
