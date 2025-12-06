"""
Unit tests for ProductRepository and PriceRepository
Tests database operations, queries, and bulk upserts
"""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MicrosoftPrice, MicrosoftProduct
from src.repositories.product_repository import PriceRepository, ProductRepository


@pytest.mark.asyncio
class TestProductRepository:
    """Test suite for ProductRepository"""

    async def test_get_by_product_sku_found(self, db_session: AsyncSession):
        """Test get product by product_id and sku_id"""
        repo = ProductRepository(db_session)

        # Create test product
        product = MicrosoftProduct(
            product_id="TEST_PROD",
            sku_id="TEST_SKU",
            product_title="Test Product",
            sku_title="Test SKU",
            publisher="Microsoft",
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.commit()

        result = await repo.get_by_product_sku("TEST_PROD", "TEST_SKU")

        assert result is not None
        assert result.product_id == "TEST_PROD"
        assert result.sku_id == "TEST_SKU"

    async def test_get_by_product_sku_not_found(self, db_session: AsyncSession):
        """Test get product returns None when not found"""
        repo = ProductRepository(db_session)
        result = await repo.get_by_product_sku("NONEXISTENT", "SKU")
        assert result is None

    async def test_search_products_by_title(self, db_session: AsyncSession):
        """Test search products by title"""
        repo = ProductRepository(db_session)

        # Create test products
        product1 = MicrosoftProduct(
            product_id="P1",
            sku_id="S1",
            product_title="Office 365",
            sku_title="E3",
            publisher="Microsoft",
        )
        product2 = MicrosoftProduct(
            product_id="P2",
            sku_id="S2",
            product_title="Microsoft 365",
            sku_title="E5",
            publisher="Microsoft",
        )
        db_session.add_all([product1, product2])
        await db_session.commit()

        results = await repo.search_products("Office", limit=10)

        assert len(results) >= 1
        assert any("Office" in p.product_title for p in results)


@pytest.mark.asyncio
class TestPriceRepository:
    """Test suite for PriceRepository"""

    async def test_get_current_price_found(self, db_session: AsyncSession):
        """Test get current price for SKU"""
        repo = PriceRepository(db_session)

        # Create test product first
        product = MicrosoftProduct(
            product_id="PROD1",
            sku_id="SKU1",
            product_title="Test",
            sku_title="Test",
            publisher="Microsoft",
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.commit()

        # Create test price
        price = MicrosoftPrice(
            product_id="PROD1",
            sku_id="SKU1",
            market="FR",
            currency="EUR",
            segment="Commercial",
            term_duration="P1M",
            billing_plan="Monthly",
            unit_price=Decimal("10.00"),
            erp_price=Decimal("12.00"),
            effective_start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            effective_end_date=datetime(2099, 12, 31, tzinfo=timezone.utc),
        )
        db_session.add(price)
        await db_session.commit()

        result = await repo.get_current_price(
            sku_id="SKU1", market="FR", currency="EUR", segment="Commercial"
        )

        assert result is not None
        assert result.unit_price == Decimal("10.00")

    async def test_upsert_bulk_insert(self, db_session: AsyncSession):
        """Test bulk insert new prices"""
        repo = PriceRepository(db_session)

        # Create product first
        product = MicrosoftProduct(
            product_id="PROD2",
            sku_id="SKU2",
            product_title="Test",
            sku_title="Test",
            publisher="Microsoft",
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.commit()

        prices = [
            {
                "product_id": "PROD2",
                "sku_id": "SKU2",
                "market": "FR",
                "currency": "EUR",
                "segment": "Commercial",
                "term_duration": "P1M",
                "billing_plan": "Monthly",
                "unit_price": Decimal("15.00"),
                "erp_price": Decimal("18.00"),
                "effective_start_date": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "effective_end_date": datetime(2099, 12, 31, tzinfo=timezone.utc),
            }
        ]

        count = await repo.upsert_bulk(prices)

        assert count == 1

    async def test_get_price_history(self, db_session: AsyncSession):
        """Test get price history for SKU"""
        repo = PriceRepository(db_session)

        # Setup test data
        product = MicrosoftProduct(
            product_id="PROD3",
            sku_id="SKU3",
            product_title="Test",
            sku_title="Test",
            publisher="Microsoft",
        )
        db_session.add(product)
        await db_session.commit()

        # Multiple prices over time
        prices = [
            MicrosoftPrice(
                product_id="PROD3",
                sku_id="SKU3",
                market="FR",
                currency="EUR",
                segment="Commercial",
                term_duration="P1M",
                billing_plan="Monthly",
                unit_price=Decimal("10.00"),
                erp_price=Decimal("12.00"),
                effective_start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
                effective_end_date=datetime(2024, 6, 30, tzinfo=timezone.utc),
            ),
            MicrosoftPrice(
                product_id="PROD3",
                sku_id="SKU3",
                market="FR",
                currency="EUR",
                segment="Commercial",
                term_duration="P1M",
                billing_plan="Monthly",
                unit_price=Decimal("11.00"),
                erp_price=Decimal("13.00"),
                effective_start_date=datetime(2024, 7, 1, tzinfo=timezone.utc),
                effective_end_date=datetime(2099, 12, 31, tzinfo=timezone.utc),
            ),
        ]
        db_session.add_all(prices)
        await db_session.commit()

        history = await repo.get_price_history(
            sku_id="SKU3", market="FR", currency="EUR", limit=10
        )

        assert len(history) == 2
        # Most recent first
        assert history[0].unit_price == Decimal("11.00")
