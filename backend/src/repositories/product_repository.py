"""
Repository for Microsoft Product pricing data
Handles database operations for microsoft_products and microsoft_prices tables
"""
from datetime import date, datetime
from typing import Optional, Sequence

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..models import MicrosoftPrice, MicrosoftProduct
from .base import BaseRepository


class ProductRepository(BaseRepository[MicrosoftProduct]):
    """Repository for microsoft_products table"""

    def __init__(self, session: AsyncSession):
        super().__init__(MicrosoftProduct, session)

    async def get_by_product_sku(
        self, product_id: str, sku_id: str
    ) -> Optional[MicrosoftProduct]:
        """Get product by product_id and sku_id"""
        query = select(MicrosoftProduct).where(
            and_(
                MicrosoftProduct.product_id == product_id,
                MicrosoftProduct.sku_id == sku_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search_products(
        self, search_term: Optional[str] = None, limit: int = 100
    ) -> Sequence[MicrosoftProduct]:
        """Search products by title or description"""
        query = select(MicrosoftProduct)

        if search_term:
            search_filter = or_(
                MicrosoftProduct.product_title.ilike(f"%{search_term}%"),
                MicrosoftProduct.sku_title.ilike(f"%{search_term}%"),
                MicrosoftProduct.sku_description.ilike(f"%{search_term}%"),
            )
            query = query.where(search_filter)

        query = query.limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()


class PriceRepository(BaseRepository[MicrosoftPrice]):
    """Repository for microsoft_prices table"""

    def __init__(self, session: AsyncSession):
        super().__init__(MicrosoftPrice, session)

    async def get_current_price(
        self,
        sku_id: str,
        market: str,
        currency: str,
        segment: str = "Commercial",
        effective_date: Optional[date] = None,
    ) -> Optional[MicrosoftPrice]:
        """
        Get current/effective price for a SKU in specific market

        Args:
            sku_id: SKU identifier
            market: Market code (e.g., 'FR', 'AX')
            currency: Currency code (e.g., 'EUR')
            segment: Customer segment (default: 'Commercial')
            effective_date: Date to check pricing for (default: today)

        Returns:
            Most recent applicable price or None
        """
        if effective_date is None:
            effective_date = datetime.now().date()

        query = (
            select(MicrosoftPrice)
            .where(
                and_(
                    MicrosoftPrice.sku_id == sku_id,
                    MicrosoftPrice.market == market,
                    MicrosoftPrice.currency == currency,
                    MicrosoftPrice.segment == segment,
                    MicrosoftPrice.effective_start_date <= effective_date,
                    MicrosoftPrice.effective_end_date >= effective_date,
                )
            )
            .order_by(MicrosoftPrice.effective_start_date.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_price_history(
        self,
        sku_id: str,
        market: str,
        currency: str,
        limit: int = 10,
    ) -> Sequence[MicrosoftPrice]:
        """Get price history for a SKU"""
        query = (
            select(MicrosoftPrice)
            .where(
                and_(
                    MicrosoftPrice.sku_id == sku_id,
                    MicrosoftPrice.market == market,
                    MicrosoftPrice.currency == currency,
                )
            )
            .order_by(MicrosoftPrice.effective_start_date.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def upsert_bulk(self, prices: list[dict]) -> int:
        """
        Bulk upsert pricing data using PostgreSQL ON CONFLICT

        Args:
            prices: List of price dictionaries

        Returns:
            Number of rows affected
        """
        if not prices:
            return 0

        stmt = insert(MicrosoftPrice).values(prices)
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                "product_id",
                "sku_id",
                "market",
                "currency",
                "segment",
                "billing_plan",
                "effective_start_date",
            ],
            set_={
                "unit_price": stmt.excluded.unit_price,
                "erp_price": stmt.excluded.erp_price,
                "effective_end_date": stmt.excluded.effective_end_date,
                "change_indicator": stmt.excluded.change_indicator,
                "updated_at": func.now(),
            },
        )

        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def delete_outdated_prices(self, cutoff_date: datetime) -> int:
        """Delete prices older than cutoff date"""
        stmt = delete(MicrosoftPrice).where(
            MicrosoftPrice.effective_end_date < cutoff_date
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
