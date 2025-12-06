"""
CSV Import Service for Microsoft Pricing Data - OPTIMIZED VERSION V2
Handles importing Partner Center pricing CSV files into the database
"""
import asyncio
import csv
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, TypedDict

import aiofiles
import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.microsoft_price import MicrosoftPrice
from ..models.microsoft_product import MicrosoftProduct


class ImportStats(TypedDict):
    products: int
    prices: int
    errors: List[str]
    products_skipped: int
    prices_skipped: int
    batches_processed: int
    total_time: float

class BatchStats(TypedDict, total=False):
    products: int
    prices: int
    errors: List[str]
    products_skipped: int
    prices_skipped: int
    batches_processed: int
    total_time: float

logger = structlog.get_logger(__name__)


class PriceImportService:
    """
    Service for importing Microsoft pricing data from CSV files - VERSION OPTIMISÉE V2

    Optimisations majeures :
    1. Pré-chargement intelligent des produits existants
    2. Bulk insert avec ON CONFLICT pour éviter les vérifications individuelles
    3. Streaming CSV pour gérer de gros fichiers sans saturer la mémoire
    4. Batch processing optimal (1000 lignes par batch)
    5. Indexation en mémoire pour les vérifications rapides
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logger
        self.batch_size = 1000  # Taille optimale pour PostgreSQL

    async def import_csv(self, csv_path: Path) -> dict[str, Any]:
        """
        Import pricing data from CSV file - VERSION OPTIMISÉE V2
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        stats: ImportStats = {
            "products": 0, "prices": 0, "errors": [],
            "products_skipped": 0, "prices_skipped": 0,
            "batches_processed": 0,
            "total_time": 0.0
        }

        self.logger.info("csv_import_started_v2", file=str(csv_path))

        try:
            # Étape 1: Pré-chargement intelligent des produits existants
            existing_products = await self._load_existing_products()
            self.logger.info("existing_products_loaded_v2", count=len(existing_products))

            # Étape 2: Streaming CSV avec batch processing
            batch_stats = await self._process_csv_streaming(csv_path, existing_products)

            # Fusionner les statistiques
            # Fusionner les statistiques
            stats["products"] += batch_stats.get("products", 0)
            stats["prices"] += batch_stats.get("prices", 0)
            stats["products_skipped"] += batch_stats.get("products_skipped", 0)
            stats["prices_skipped"] += batch_stats.get("prices_skipped", 0)
            stats["batches_processed"] += batch_stats.get("batches_processed", 0)
            stats["errors"].extend(batch_stats.get("errors", []))

            await self.db.commit()

            self.logger.info(
                "csv_import_completed_v2",
                products_inserted=stats["products"],
                products_skipped=stats["products_skipped"],
                prices_inserted=stats["prices"],
                prices_skipped=stats["prices_skipped"],
                batches_processed=stats["batches_processed"],
                errors_count=len(stats["errors"]),
                total_time=stats.get("total_time", 0)
            )

        except Exception as e:
            await self.db.rollback()
            self.logger.error("csv_import_failed_v2", error=str(e), exc_info=True)
            raise

        return dict(stats)

    async def _load_existing_products(self) -> Set[Tuple[str, str]]:
        """
        Charger uniquement les clés des produits existants pour économiser la mémoire
        """
        stmt = select(MicrosoftProduct.product_id, MicrosoftProduct.sku_id)
        result = await self.db.execute(stmt)

        # Retourner un set de tuples pour accès O(1)
        # Explicit typing/casting for mypy
        rows = result.all()
        return set((str(row[0]), str(row[1])) for row in rows)

    async def _process_csv_streaming(
        self, csv_path: Path, existing_products: Set[Tuple[str, str]]
    ) -> BatchStats:
        """
        Traiter le CSV en streaming avec batch processing optimal
        """
        stats: BatchStats = {
            "products": 0, "prices": 0, "errors": [],
            "products_skipped": 0, "prices_skipped": 0,
            "batches_processed": 0, "total_time": 0
        }

        start_time = time.time()

        products_batch: List[MicrosoftProduct] = []
        prices_batch: List[MicrosoftPrice] = []
        seen_products: Set[Tuple[str, str]] = set()  # Pour éviter les doublons dans le batch

        async with aiofiles.open(csv_path, mode="r", encoding="utf-8") as file:
            # Lire l'en-tête
            header_line = await file.readline()
            if not header_line:
                raise ValueError("CSV file is empty")

            reader = csv.DictReader([header_line])
            fieldnames = reader.fieldnames

            line_num = 1
            async for line in file:
                line_num += 1
                try:
                    # Parser la ligne
                    # Ensure fieldnames is iterable
                    headers = fieldnames if fieldnames else []
                    values = csv.reader([line]).__next__()
                    row = dict(zip(headers, values))

                    # Créer les objets
                    product = self._parse_product(row)
                    price = self._parse_price(row)

                    product_key = (product.product_id, product.sku_id)

                    # Gestion intelligente des produits
                    if product_key not in existing_products and product_key not in seen_products:
                        products_batch.append(product)
                        seen_products.add(product_key)
                        stats["products"] += 1
                    else:
                        stats["products_skipped"] += 1

                    # Toujours ajouter les prix (ils peuvent avoir des variations)
                    prices_batch.append(price)
                    stats["prices"] += 1

                    # Traiter le batch quand il atteint la taille optimale
                    if len(products_batch) >= self.batch_size or len(prices_batch) >= self.batch_size:
                        await self._process_batch(products_batch, prices_batch)
                        stats["batches_processed"] += 1

                        # Réinitialiser les batchs
                        products_batch = []
                        prices_batch = []
                        seen_products = set()

                        # Petit pause pour éviter de surcharger la base de données
                        await asyncio.sleep(0.01)

                except Exception as e:
                    error_msg = f"Line {line_num}: {str(e)}"
                    stats["errors"].append(error_msg)
                    self.logger.warning("csv_row_error_v2", line=line_num, error=str(e))

        # Traiter le dernier batch
        if products_batch or prices_batch:
            await self._process_batch(products_batch, prices_batch)
            stats["batches_processed"] += 1

        stats["total_time"] = time.time() - start_time
        return stats

    async def _process_batch(
        self, products: List[MicrosoftProduct], prices: List[MicrosoftPrice]
    ) -> None:
        """
        Traiter un batch de produits et prix
        """
        if products:
            await self._bulk_insert_products(products)

        if prices:
            await self._bulk_insert_prices(prices)

    async def _bulk_insert_products(self, products: List[MicrosoftProduct]) -> None:
        """
        Bulk insert products avec ON CONFLICT - ultra optimisé
        """
        if not products:
            return

        # Utiliser PostgreSQL INSERT ... ON CONFLICT DO NOTHING
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
        ]).on_conflict_do_nothing(constraint="uq_product_sku")

        await self.db.execute(stmt)

    async def _bulk_insert_prices(self, prices: List[MicrosoftPrice]) -> None:
        """
        Bulk insert prices avec ON CONFLICT - ultra optimisé
        """
        if not prices:
            return

        # Utiliser PostgreSQL INSERT ... ON CONFLICT DO NOTHING
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
        ]).on_conflict_do_nothing(constraint="uq_price_variant")

        await self.db.execute(stmt)

    def _parse_product(self, row: Dict[str, str]) -> MicrosoftProduct:
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

    def _parse_price(self, row: Dict[str, str]) -> MicrosoftPrice:
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
