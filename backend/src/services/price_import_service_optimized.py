"""
CSV Import Service for Microsoft Pricing Data - OPTIMIZED VERSION
Handles importing Partner Center pricing CSV files into the database
"""
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import aiofiles  # type: ignore[import-untyped]
import structlog
from sqlalchemy import select, insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import MicrosoftPrice, MicrosoftProduct

logger = structlog.get_logger(__name__)


class PriceImportServiceOptimized:
    """
    Service for importing Microsoft pricing data from CSV files - OPTIMIZED VERSION

    Processes CSV files from Partner Center and imports them into
    microsoft_products and microsoft_prices tables.

    Optimizations:
    - Pre-loading of existing products (single query)
    - Bulk insert with ON CONFLICT for products
    - Streaming CSV reading
    - Batch processing
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logger

    async def import_csv(self, csv_path: Path) -> dict[str, Any]:
        """
        Import pricing data from CSV file - OPTIMIZED VERSION

        Args:
            csv_path: Path to the CSV file

        Returns:
            Dictionary with import statistics
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        stats: dict[str, Any] = {"products": 0, "prices": 0, "errors": [], "skipped": 0}
        
        self.logger.info("csv_import_started_optimized", file=str(csv_path))

        try:
            # Pré-chargement des produits existants - OPTIMISATION #1
            existing_products = await self._load_existing_products()
            self.logger.info("existing_products_loaded", count=len(existing_products))

            # Traitement streaming du CSV - OPTIMISATION #2
            products_to_insert = []
            prices_to_insert = []
            
            async with aiofiles.open(csv_path, mode="r", encoding="utf-8") as file:
                # Lecture ligne par ligne au lieu de tout charger en mémoire
                header_line = await file.readline()
                if not header_line:
                    raise ValueError("CSV file is empty")
                
                reader = csv.DictReader([header_line])
                fieldnames = reader.fieldnames
                
                line_num = 1
                async for line in file:
                    line_num += 1
                    try:
                        # Parser la ligne manuellement pour éviter de charger tout le fichier
                        row = dict(zip(fieldnames, csv.reader([line]).__next__()))
                        
                        # Parse and create objects
                        product = self._parse_product(row)
                        price = self._parse_price(row)

                        # Vérifier si le produit existe déjà (en mémoire, pas en DB)
                        product_key = (product.product_id, product.sku_id)
                        if product_key not in existing_products:
                            products_to_insert.append(product)
                            existing_products[product_key] = product  # Éviter les doublons
                        
                        # Toujours ajouter le prix
                        prices_to_insert.append(price)
                        
                        # Traitement par lots de 1000 - OPTIMISATION #3
                        if len(products_to_insert) >= 1000:
                            await self._bulk_insert_products(products_to_insert)
                            stats["products"] += len(products_to_insert)
                            products_to_insert = []
                            
                        if len(prices_to_insert) >= 1000:
                            await self._bulk_insert_prices(prices_to_insert)
                            stats["prices"] += len(prices_to_insert)
                            prices_to_insert = []

                    except Exception as e:
                        error_msg = f"Line {line_num}: {str(e)}"
                        stats["errors"].append(error_msg)
                        self.logger.warning(
                            "csv_row_error", line=line_num, error=str(e)
                        )

            # Traiter les derniers lots
            if products_to_insert:
                await self._bulk_insert_products(products_to_insert)
                stats["products"] += len(products_to_insert)
                
            if prices_to_insert:
                await self._bulk_insert_prices(prices_to_insert)
                stats["prices"] += len(prices_to_insert)

            await self.db.commit()

            self.logger.info(
                "csv_import_completed_optimized",
                products=stats["products"],
                prices=stats["prices"],
                errors_count=len(stats["errors"]),
            )

        except Exception as e:
            await self.db.rollback()
            self.logger.error("csv_import_failed", error=str(e), exc_info=True)
            raise

        return stats

    async def _load_existing_products(self) -> dict[tuple[str, str], MicrosoftProduct]:
        """
        Load all existing products into memory - OPTIMISATION #1
        Une seule requête au lieu d'une par produit
        """
        stmt = select(MicrosoftProduct)
        result = await self.db.execute(stmt)
        products = result.scalars().all()
        
        # Créer un dictionnaire pour accès rapide
        return {(p.product_id, p.sku_id): p for p in products}

    async def _bulk_insert_products(self, products: list[MicrosoftProduct]) -> None:
        """
        Bulk insert products with ON CONFLICT - OPTIMISATION #2
        """
        if not products:
            return
            
        # Utiliser PostgreSQL INSERT ... ON CONFLICT
        stmt = pg_insert(MicrosoftProduct).values([
            {
                "product_id": p.product_id,
                "sku_id": p.sku_id,
                "product_title": p.product_title,
                "sku_title": p.sku_title,
                "publisher": p.publisher,
                "sku_description": p.sku_description,
                "unit_of_measure": p.unit_of_measure,
                "tags": p.tags,
            }
            for p in products
        ])
        
        # On conflict, do nothing (le produit existe déjà)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_product_sku"  # Nom de la contrainte unique
        )
        
        await self.db.execute(stmt)

    async def _bulk_insert_prices(self, prices: list[MicrosoftPrice]) -> None:
        """
        Bulk insert prices - OPTIMISATION #3
        """
        if not prices:
            return
            
        # Utiliser PostgreSQL INSERT ... ON CONFLICT pour les prix aussi
        stmt = pg_insert(MicrosoftPrice).values([
            {
                "product_id": p.product_id,
                "sku_id": p.sku_id,
                "market": p.market,
                "currency": p.currency,
                "segment": p.segment,
                "term_duration": p.term_duration,
                "billing_plan": p.billing_plan,
                "unit_price": p.unit_price,
                "erp_price": p.erp_price,
                "effective_start_date": p.effective_start_date,
                "effective_end_date": p.effective_end_date,
                "change_indicator": p.change_indicator,
                "pricing_tier_range_min": p.pricing_tier_range_min,
                "pricing_tier_range_max": p.pricing_tier_range_max,
            }
            for p in prices
        ])
        
        # On conflict, do nothing (le prix existe déjà)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_price_variant"  # Nom de la contrainte unique
        )
        
        await self.db.execute(stmt)

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
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    @staticmethod
    def _parse_billing_plan(billing_plan: str) -> str:
        """Parse and validate billing plan value"""
        if not billing_plan or billing_plan.strip() == "":
            return "Annual"
        
        if billing_plan.strip() == "None":
            return "Annual"
        
        billing_plan_clean = billing_plan.strip()
        if billing_plan_clean not in ["Annual", "Monthly"]:
            logger.warning(
                "invalid_billing_plan_value", value=billing_plan_clean, default="Annual"
            )
            return "Annual"
        
        return billing_plan_clean

    @staticmethod
    def _parse_int(value: str | None) -> int | None:
        """Safely parse integer from string"""
        if not value or value.strip() == "":
            return None
        return int(value)