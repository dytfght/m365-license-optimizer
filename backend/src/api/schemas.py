"""
Pydantic schemas for API requests/responses
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Tenant schemas
class TenantCreate(BaseModel):
    """Schema for creating a tenant"""
    name: str = Field(..., min_length=1, max_length=255)
    tenant_id: str = Field(..., min_length=36, max_length=36, description="Azure AD Tenant ID")
    country: str = Field(..., min_length=2, max_length=2, description="ISO country code")
    client_id: str = Field(..., min_length=36, max_length=36, description="App Registration client ID")
    client_secret: str = Field(..., min_length=1, description="App Registration client secret")
    scopes: list[str] = Field(
        default=[
            "User.Read.All",
            "Directory.Read.All",
            "Reports.Read.All",
            "Organization.Read.All",
        ],
        description="Graph API scopes"
    )
    default_language: str = Field(default="fr", pattern="^(fr|en)$")
    csp_customer_id: Optional[str] = Field(None, max_length=36)


class TenantResponse(BaseModel):
    """Schema for tenant response"""
    model_config = ConfigDict(from_attributes=True)  # ← AJOUTER CETTE LIGNE
    
    id: UUID
    name: str
    tenant_id: str
    country: Optional[str] = None  # ✓ OK
    status: str
    created_at: datetime  # ✓ OK


class TenantDetailResponse(TenantResponse):
    """Schema for detailed tenant response"""
    default_language: str
    app_registration: Optional[dict] = None


# User sync schemas
class UserSyncResponse(BaseModel):
    """Schema for user sync response"""
    synced: int
    created: int
    updated: int
    duration_seconds: float


# Validation schemas
class ValidationResponse(BaseModel):
    """Schema for credential validation response"""
    valid: bool
    organization: Optional[str] = None
    tenant_id: Optional[str] = None
    error: Optional[str] = None
