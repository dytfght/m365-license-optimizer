"""
Pydantic schemas for Tenant models
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    """Base tenant schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    country: str = Field(
        ..., min_length=2, max_length=2, description="Country code (ISO 3166-1 alpha-2)"
    )
    default_language: str = Field(default="fr", description="Language code (fr/en)")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""

    tenant_id: str = Field(..., description="Azure AD tenant ID")
    csp_customer_id: str | None = Field(None, description="CSP customer ID")


class TenantCreateRequest(TenantCreate):
    """Schema for creating a tenant with app registration details"""

    client_id: str = Field(..., description="App Client ID")
    client_secret: str = Field(..., description="App Client Secret")
    scopes: list[str] = Field(default_factory=list, description="App Permissions")
    authority_url: str | None = Field(None, description="Authority URL")


class TenantUpdate(BaseModel):
    """Schema for updating a tenant"""

    name: str | None = None
    country: str | None = None
    language: str | None = None
    onboarding_status: str | None = None


class AppRegistrationResponse(BaseModel):
    """Response schema for app registration"""

    client_id: str
    authority_url: str | None
    scopes: list[str]
    consent_status: str


class TenantResponse(TenantBase):
    """Response schema for tenant data"""

    id: UUID = Field(..., description="Internal tenant ID")
    tenant_id: str = Field(..., description="Azure AD tenant ID")
    onboarding_status: str = Field(..., description="Onboarding status")
    csp_customer_id: str | None = Field(None, description="CSP customer ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    app_registration: AppRegistrationResponse | None = None

    class Config:
        from_attributes = True


class TenantList(BaseModel):
    """Response schema for list of tenants"""

    tenants: list[TenantResponse] = Field(..., description="List of tenants")
    total: int = Field(..., description="Total number of tenants")
