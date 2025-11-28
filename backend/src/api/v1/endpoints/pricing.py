"""
API endpoints for Microsoft Partner Center pricing
"""
from pathlib import Path
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.database import get_db
from src.models.user import User
from src.repositories.product_repository import PriceRepository, ProductRepository
from src.schemas.pricing import (
    MicrosoftPriceResponse,
    MicrosoftProductResponse,
    PriceImportStats,
)
from src.services.price_import_service import PriceImportService

router = APIRouter(prefix="/pricing", tags=["pricing"])
logger = structlog.get_logger(__name__)


@router.post(
    "/import", response_model=PriceImportStats, status_code=status.HTTP_202_ACCEPTED
)
async def import_pricing_csv(
    file: UploadFile = File(..., description="CSV file with Microsoft pricing data"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PriceImportStats:
    """
    Import Microsoft pricing data from CSV file

    **Authentication**: Requires JWT token
    **Rate limit**: Not implemented (TODO)

    The CSV file should follow the Partner Center pricing format with columns:
    - ProductId, SkuId, ProductTitle, SkuTitle, Publisher
    - Market, Currency, Segment, TermDuration, BillingPlan
    - UnitPrice, ERP Price, EffectiveStartDate, EffectiveEndDate
    - etc.

    Returns statistics about the import process.
    """
    # Validate file extension
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted",
        )

    logger.info(
        "pricing_import_started",
        filename=file.filename,
        user_id=str(current_user.id),
    )

    # Save uploaded file temporarily
    temp_path = Path(f"/tmp/pricing_import_{current_user.id}_{file.filename}")
    try:
        # Write file to disk
        content = await file.read()
        temp_path.write_bytes(content)

        # Import via service
        service = PriceImportService(db)
        stats = await service.import_csv(temp_path)

        logger.info(
            "pricing_import_completed",
            filename=file.filename,
            products=stats["products"],
            prices=stats["prices"],
            errors=len(stats["errors"]),
        )

        return stats  # type: ignore[return-value]

    except Exception as e:
        logger.error(
            "pricing_import_failed",
            filename=file.filename,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


@router.get("/products", response_model=list[MicrosoftProductResponse])
async def list_products(
    search: Optional[str] = Query(None, description="Search term for product title"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
) -> list[MicrosoftProductResponse]:
    """
    List Microsoft products with optional search

    Search term is matched against:
    - Product title
    - SKU title
    - SKU description
    """
    repo = ProductRepository(db)
    products = await repo.search_products(search_term=search, limit=limit)
    return products  # type: ignore


@router.get("/products/{product_id}/{sku_id}", response_model=MicrosoftProductResponse)
async def get_product(
    product_id: str,
    sku_id: str,
    db: AsyncSession = Depends(get_db),
) -> MicrosoftProductResponse:
    """Get specific product by product_id and sku_id"""
    repo = ProductRepository(db)
    product = await repo.get_by_product_sku(product_id, sku_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product not found: {product_id}/{sku_id}",
        )

    return product  # type: ignore


@router.get(
    "/products/{product_id}/{sku_id}/prices",
    response_model=list[MicrosoftPriceResponse],
)
async def get_product_prices(
    product_id: str,
    sku_id: str,
    market: Optional[str] = Query(None, description="Market code (e.g., FR, AX)"),
    currency: Optional[str] = Query(None, description="Currency code (e.g., EUR)"),
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[MicrosoftPriceResponse]:
    """
    Get price history for a product

    Optionally filter by market and currency
    """
    repo = PriceRepository(db)

    if market and currency:
        prices = await repo.get_price_history(
            sku_id=sku_id, market=market, currency=currency, limit=limit
        )
    else:
        # Get all prices for product (not filtered by market/currency)
        from sqlalchemy import select

        from src.models import MicrosoftPrice

        query = (
            select(MicrosoftPrice)
            .where(MicrosoftPrice.sku_id == sku_id)
            .order_by(MicrosoftPrice.effective_start_date.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        prices = list(result.scalars().all())

    return prices  # type: ignore


@router.get("/prices/current", response_model=Optional[MicrosoftPriceResponse])
async def get_current_price(
    sku_id: str = Query(..., description="SKU ID"),
    market: str = Query(..., description="Market code"),
    currency: str = Query(..., description="Currency code"),
    segment: str = Query("Commercial", description="Customer segment"),
    db: AsyncSession = Depends(get_db),
) -> Optional[MicrosoftPriceResponse]:
    """
    Get current effective price for a SKU

    Returns the price effective as of today for the specified:
    - SKU ID
    - Market
    - Currency
    - Customer segment
    """
    repo = PriceRepository(db)
    price = await repo.get_current_price(
        sku_id=sku_id, market=market, currency=currency, segment=segment
    )

    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No current price found for {sku_id} in {market}/{currency}",
        )

    return price  # type: ignore
