"""
CSV Import Service for Microsoft Pricing Data
Handles importing Partner Center pricing CSV files into the database
"""
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import aiofiles  # type: ignore[import-untyped]
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MicrosoftPrice, MicrosoftProduct

logger = structlog.get_logger(__name__)


class PriceImportService:
    """
    Service for importing Microsoft pricing data from CSV files

    Processes CSV files from Partner Center and imports them into
    microsoft_products and microsoft_prices tables.

    Features:
    - Bulk upsert for products (avoids duplicates)
    - Bulk insert for prices
    - Error handling with detailed reporting
    - Transaction management
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logger

    async def import_csv(self, csv_path: Path) -> dict[str, Any]:
        """
        Import pricing data from CSV file

        Args:
            csv_path: Path to the CSV file

        Returns:
            Dictionary with import statistics:
            - products: Number of products processed
            - prices: Number of prices processed
            - errors: List of errors encountered

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        stats: dict[str, Any] = {"products": 0, "prices": 0, "errors": [], "skipped": 0}
        products_map: dict[tuple[str, str], MicrosoftProduct] = {}
        prices_list: list[MicrosoftPrice] = []

        self.logger.info("csv_import_started", file=str(csv_path))

        try:
            async with aiofiles.open(csv_path, mode="r", encoding="utf-8") as file:
                content = await file.read()
                reader = csv.DictReader(content.splitlines())

                for line_num, row in enumerate(reader, start=2):  # Line 1 is header
                    try:
                        # Parse and create product/price objects
                        product = self._parse_product(row)
                        price = self._parse_price(row)

                        # Track unique products
                        product_key = (product.product_id, product.sku_id)
                        if product_key not in products_map:
                            products_map[product_key] = product

                        # Collect all prices
                        prices_list.append(price)

                    except Exception as e:
                        error_msg = f"Line {line_num}: {str(e)}"
                        stats["errors"].append(error_msg)
                        self.logger.warning(
                            "csv_row_error", line=line_num, error=str(e)
                        )

            # Bulk insert/upsert in database
            stats["products"] = await self._upsert_products(list(products_map.values()))
            stats["prices"] = await self._insert_prices(prices_list)

            await self.db.commit()

            self.logger.info(
                "csv_import_completed",
                products=stats["products"],
                prices=stats["prices"],
                errors_count=len(stats["errors"]),
            )

        except Exception as e:
            await self.db.rollback()
            self.logger.error("csv_import_failed", error=str(e), exc_info=True)
            raise

        return stats

    def _parse_product(self, row: dict[str, str]) -> MicrosoftProduct:
        """Parse CSV row into MicrosoftProduct object"""
        return MicrosoftProduct(
            product_id=row["ProductId"],
            sku_id=row["SkuId"],
            product_title=row["ProductTitle"],
            sku_title=row["SkuTitle"],
            publisher=row.get("Publisher", "Microsoft Corporation"),
            sku_description=row.get("SkuDescription"),
            unit_of_measure=row.get("UnitOfMeasure"),
            tags=[tag.strip() for tag in row.get("Tags", "").split(";") if tag.strip()],
        )

    def _parse_price(self, row: dict[str, str]) -> MicrosoftPrice:
        """Parse CSV row into MicrosoftPrice object"""
        return MicrosoftPrice(
            product_id=row["ProductId"],
            sku_id=row["SkuId"],
            market=row["Market"],
            currency=row["Currency"],
            segment=row["Segment"],
            term_duration=row["TermDuration"],
            billing_plan=self._parse_billing_plan(row["BillingPlan"]),
            unit_price=Decimal(row["UnitPrice"]),
            erp_price=Decimal(row["ERP Price"]),
            effective_start_date=self._parse_datetime(row["EffectiveStartDate"]),
            effective_end_date=self._parse_datetime(row["EffectiveEndDate"]),
            change_indicator=row.get("ChangeIndicator", "Unchanged"),
            pricing_tier_range_min=self._parse_int(row.get("PricingTierRangeMin")),
            pricing_tier_range_max=self._parse_int(row.get("PricingTierRangeMax")),
        )

    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        """Parse ISO 8601 datetime string"""
        # Format: 2024-05-01T00:00:00.0000000Z
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    @staticmethod
    def _parse_billing_plan(billing_plan: str) -> str:
        """Parse and validate billing plan value"""
        # Handle None or empty values
        if not billing_plan or billing_plan.strip() == "":
            return "Annual"  # Default to Annual
        
        # Handle "None" string from CSV
        if billing_plan.strip() == "None":
            return "Annual"  # Default to Annual
        
        # Validate against allowed values
        billing_plan_clean = billing_plan.strip()
        if billing_plan_clean not in ["Annual", "Monthly"]:
            # Log warning and default to Annual
            logger.warning(
                "invalid_billing_plan_value",
                value=billing_plan_clean,
                default="Annual"
            )
            return "Annual"
        
        return billing_plan_clean

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        """Safely parse integer from string"""
        if not value or value.strip() == "":
            return None
        return int(value)

    async def _upsert_products(self, products: list[MicrosoftProduct]) -> int:
        """
        Bulk upsert products (insert or update if exists)

        Using merge() to handle conflicts on unique constraint
        """
        count = 0
        for product in products:
            # Check if product exists
            stmt = select(MicrosoftProduct).where(
                MicrosoftProduct.product_id == product.product_id,
                MicrosoftProduct.sku_id == product.sku_id,
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                self.db.add(product)
                count += 1

        await self.db.flush()
        return count

    async def _insert_prices(self, prices: list[MicrosoftPrice]) -> int:
        """Bulk insert prices"""
        self.db.add_all(prices)
        await self.db.flush()
        return len(prices)
