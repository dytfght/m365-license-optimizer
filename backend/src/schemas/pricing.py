"""
Pydantic schemas for Microsoft Products and Pricing
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MicrosoftProductBase(BaseModel):
    """Base schema for Microsoft Product"""

    product_id: str = Field(..., max_length=50, description="Partner Center Product ID")
    sku_id: str = Field(..., max_length=50, description="Partner Center SKU ID")
    product_title: str = Field(..., max_length=500)
    sku_title: str = Field(..., max_length=500)
    publisher: str = Field(default="Microsoft Corporation", max_length=255)
    sku_description: Optional[str] = None
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    tags: Optional[list[str]] = Field(default_factory=list)


class MicrosoftProductCreate(MicrosoftProductBase):
    """Schema for creating a Microsoft Product"""

    pass


class MicrosoftProductResponse(MicrosoftProductBase):
    """Schema for Microsoft Product response"""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MicrosoftPriceBase(BaseModel):
    """Base schema for Microsoft Price"""

    product_id: str = Field(..., max_length=50)
    sku_id: str = Field(..., max_length=50)
    market: str = Field(..., max_length=5, description="Market code (e.g., AX, FR)")
    currency: str = Field(..., max_length=3, description="ISO 4217 currency code")
    segment: str = Field(..., description="Commercial, Education, or Charity")
    term_duration: str = Field(
        ..., max_length=10, description="ISO 8601 duration (P1Y, P1M)"
    )
    billing_plan: str = Field(..., description="Annual or Monthly")
    unit_price: Decimal = Field(..., decimal_places=2)
    erp_price: Decimal = Field(..., decimal_places=2)
    effective_start_date: datetime
    effective_end_date: datetime
    change_indicator: str = Field(default="Unchanged", max_length=20)
    pricing_tier_range_min: Optional[int] = None
    pricing_tier_range_max: Optional[int] = None


class MicrosoftPriceCreate(MicrosoftPriceBase):
    """Schema for creating a Microsoft Price"""

    pass


class MicrosoftPriceResponse(MicrosoftPriceBase):
    """Schema for Microsoft Price response"""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PriceImportStats(BaseModel):
    """Schema for CSV import statistics"""

    products: int = Field(..., description="Number of products processed")
    prices: int = Field(..., description="Number of prices processed")
    errors: list[str] = Field(default_factory=list, description="List of errors")
    skipped: int = Field(default=0, description="Number of rows skipped")


class PriceQueryParams(BaseModel):
    """Schema for price query parameters"""

    sku_id: Optional[str] = None
    market: Optional[str] = Field(None, max_length=5)
    currency: Optional[str] = Field(None, max_length=3)
    segment: str = Field(default="Commercial")
    effective_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
