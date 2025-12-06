"""
SKU Mapping Schemas
Pydantic models for SKU mapping and add-on compatibility
"""
from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class AddonCompatibilityBase(BaseModel):
    """Base schema for add-on compatibility"""

    addon_sku_id: str = Field(..., description="Partner Center SKU ID for the add-on")
    addon_product_id: str = Field(
        ..., description="Partner Center Product ID for the add-on"
    )
    base_sku_id: str = Field(
        ..., description="Partner Center SKU ID for compatible base SKU"
    )
    base_product_id: str = Field(
        ..., description="Partner Center Product ID for compatible base SKU"
    )
    service_type: str = Field(
        ..., description="Service type (e.g., 'Microsoft 365', 'Dynamics 365')"
    )
    addon_category: str = Field(
        ..., description="Category of add-on (e.g., 'Storage', 'Calling Plan')"
    )
    min_quantity: int = Field(default=1, ge=1, description="Minimum quantity required")
    max_quantity: Optional[int] = Field(
        None, ge=1, description="Maximum quantity allowed (null = unlimited)"
    )
    quantity_multiplier: int = Field(
        default=1, ge=1, description="Quantity must be multiple of this value"
    )
    requires_domain_validation: bool = Field(
        default=False, description="Requires domain-level validation"
    )
    requires_tenant_validation: bool = Field(
        default=False, description="Requires tenant-level validation"
    )
    validation_metadata: Optional[Dict] = Field(
        default=None, description="Additional validation metadata"
    )
    pc_metadata: Optional[Dict] = Field(
        default=None, description="Partner Center specific metadata"
    )
    is_active: bool = Field(default=True, description="Whether this mapping is active")
    effective_date: Optional[datetime] = Field(
        None, description="Date when this mapping becomes effective"
    )
    expiration_date: Optional[datetime] = Field(
        None, description="Date when this mapping expires"
    )
    description: Optional[str] = Field(
        None, description="Description of the compatibility mapping"
    )
    notes: Optional[str] = Field(None, description="Internal notes about this mapping")


class AddonCompatibilityCreate(AddonCompatibilityBase):
    """Schema for creating add-on compatibility"""

    pass


class AddonCompatibilityUpdate(BaseModel):
    """Schema for updating add-on compatibility"""

    addon_sku_id: Optional[str] = Field(
        None, description="Partner Center SKU ID for the add-on"
    )
    addon_product_id: Optional[str] = Field(
        None, description="Partner Center Product ID for the add-on"
    )
    base_sku_id: Optional[str] = Field(
        None, description="Partner Center SKU ID for compatible base SKU"
    )
    base_product_id: Optional[str] = Field(
        None, description="Partner Center Product ID for compatible base SKU"
    )
    service_type: Optional[str] = Field(None, description="Service type")
    addon_category: Optional[str] = Field(None, description="Category of add-on")
    min_quantity: Optional[int] = Field(
        None, ge=1, description="Minimum quantity required"
    )
    max_quantity: Optional[int] = Field(
        None, ge=1, description="Maximum quantity allowed"
    )
    quantity_multiplier: Optional[int] = Field(
        None, ge=1, description="Quantity must be multiple of this value"
    )
    requires_domain_validation: Optional[bool] = Field(
        None, description="Requires domain-level validation"
    )
    requires_tenant_validation: Optional[bool] = Field(
        None, description="Requires tenant-level validation"
    )
    validation_metadata: Optional[Dict] = Field(
        None, description="Additional validation metadata"
    )
    pc_metadata: Optional[Dict] = Field(
        None, description="Partner Center specific metadata"
    )
    is_active: Optional[bool] = Field(
        None, description="Whether this mapping is active"
    )
    effective_date: Optional[datetime] = Field(
        None, description="Date when this mapping becomes effective"
    )
    expiration_date: Optional[datetime] = Field(
        None, description="Date when this mapping expires"
    )
    description: Optional[str] = Field(
        None, description="Description of the compatibility mapping"
    )
    notes: Optional[str] = Field(None, description="Internal notes about this mapping")


class AddonCompatibilityResponse(AddonCompatibilityBase):
    """Schema for add-on compatibility response"""

    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SkuMappingResponse(BaseModel):
    """Schema for SKU mapping response"""

    graph_sku_id: str = Field(..., description="Graph API SKU ID")
    partner_product: Optional[Dict] = Field(
        None, description="Partner Center product details"
    )
    mapping_status: str = Field(
        ..., description="Mapping status (mapped, not_found, etc.)"
    )
    last_sync_date: Optional[datetime] = Field(
        None, description="Last synchronization date"
    )


class SkuMappingSummary(BaseModel):
    """Schema for SKU mapping summary"""

    total_partner_center_products: int = Field(
        ..., description="Total Partner Center products"
    )
    total_compatibility_mappings: int = Field(
        ..., description="Total compatibility mappings"
    )
    active_mappings: int = Field(..., description="Number of active mappings")
    service_type_distribution: Dict[str, int] = Field(
        ..., description="Distribution by service type"
    )
    addon_category_distribution: Dict[str, int] = Field(
        ..., description="Distribution by add-on category"
    )
    mapping_coverage: float = Field(
        ..., description="Coverage ratio of active mappings"
    )


class AddonValidationRequest(BaseModel):
    """Schema for add-on validation request"""

    addon_sku_id: str = Field(..., description="Partner Center SKU ID for the add-on")
    base_sku_id: str = Field(
        ..., description="Partner Center SKU ID for the base product"
    )
    quantity: int = Field(..., ge=1, description="Quantity of add-ons to validate")
    tenant_id: Optional[str] = Field(None, description="Microsoft tenant ID")
    domain_name: Optional[str] = Field(None, description="Domain name for validation")


class AddonValidationResponse(BaseModel):
    """Schema for add-on validation response"""

    is_valid: bool = Field(..., description="Whether the add-on is valid")
    errors: List[str] = Field(
        default_factory=list, description="List of validation errors"
    )
    addon_sku_id: str = Field(..., description="Add-on SKU ID that was validated")
    base_sku_id: str = Field(..., description="Base SKU ID that was validated")
    quantity: int = Field(..., description="Quantity that was validated")
    validation_requirements: Optional[Dict] = Field(
        None, description="Validation requirements details"
    )


class AddonRecommendationResponse(BaseModel):
    """Schema for add-on recommendation response"""

    addon_sku_id: str = Field(..., description="Recommended add-on SKU ID")
    addon_name: str = Field(..., description="Name of the recommended add-on")
    addon_category: str = Field(..., description="Category of the recommended add-on")
    service_type: str = Field(..., description="Service type")
    compatibility_score: float = Field(..., description="Compatibility score (0-1)")
    min_quantity: int = Field(..., description="Minimum quantity required")
    max_quantity: Optional[int] = Field(None, description="Maximum quantity allowed")
    reason: str = Field(..., description="Reason for recommendation")
    estimated_savings: Optional[float] = Field(
        default=None, description="Estimated monthly savings"
    )


class BulkAddonValidationRequest(BaseModel):
    """Schema for bulk add-on validation request"""

    addons: List[Dict[str, Union[str, int, None]]] = Field(
        ..., description="List of add-ons with sku_id and quantity"
    )
    base_sku_id: str = Field(..., description="Base SKU ID for all add-ons")
    tenant_id: Optional[str] = Field(None, description="Microsoft tenant ID")
    domain_name: Optional[str] = Field(None, description="Domain name for validation")


class BulkAddonValidationResponse(BaseModel):
    """Schema for bulk add-on validation response"""

    all_valid: bool = Field(..., description="Whether all add-ons are valid")
    validation_results: Dict[str, Dict[str, Union[str, int, bool]]] = Field(
        ..., description="Validation results by SKU ID"
    )
    summary: Dict[str, int] = Field(..., description="Summary statistics")


class SkuInfoResponse(BaseModel):
    """Schema for SKU information response"""

    sku_id: str = Field(..., description="SKU ID")
    name: str = Field(..., description="SKU name")
    service_plans: List[str] = Field(
        default_factory=list, description="Service plans included"
    )
    category: str = Field(..., description="SKU category")
    partner_product_id: Optional[str] = Field(
        None, description="Partner Center Product ID"
    )
    partner_sku_id: Optional[str] = Field(None, description="Partner Center SKU ID")


class CompatibleAddonInfo(BaseModel):
    """Schema for compatible add-on information"""

    sku_id: str = Field(..., description="Add-on SKU ID")
    name: str = Field(..., description="Add-on name")
    partner_product_id: str = Field(..., description="Partner Center Product ID")
    partner_sku_id: str = Field(..., description="Partner Center SKU ID")
    service_type: str = Field(..., description="Service type")
    addon_category: str = Field(..., description="Add-on category")
    compatibility_rules: Dict[str, Union[str, int, bool, None]] = Field(
        ..., description="Compatibility rules"
    )
    validation_requirements: Optional[Dict[str, Union[str, int, bool]]] = Field(
        None, description="Validation requirements"
    )


class ValidationRequirementsResponse(BaseModel):
    """Schema for validation requirements response"""

    requires_validation: bool = Field(..., description="Whether validation is required")
    min_quantity: int = Field(..., description="Minimum quantity required")
    max_quantity: Optional[int] = Field(None, description="Maximum quantity allowed")
    quantity_multiplier: int = Field(
        ..., description="Quantity must be multiple of this value"
    )
    requires_tenant_validation: bool = Field(
        ..., description="Requires tenant validation"
    )
    requires_domain_validation: bool = Field(
        ..., description="Requires domain validation"
    )
    service_type: str = Field(..., description="Service type")
    addon_category: str = Field(..., description="Add-on category")
    is_active: bool = Field(..., description="Whether the mapping is active")
    is_available: bool = Field(
        ..., description="Whether the mapping is currently available"
    )
    validation_rules: List[str] = Field(..., description="List of validation rules")


class SkuValidationSummaryResponse(BaseModel):
    """Schema for SKU validation summary response"""

    total_compatible_addons: int = Field(
        ..., description="Total number of compatible add-ons"
    )
    active_mappings: int = Field(..., description="Number of active mappings")
    validation_requirements: Dict[str, Dict] = Field(
        ..., description="Validation requirements by SKU"
    )
    service_types: List[str] = Field(..., description="Available service types")
    addon_categories: List[str] = Field(..., description="Available add-on categories")
