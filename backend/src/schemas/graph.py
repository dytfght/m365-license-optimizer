"""
Pydantic schemas for Microsoft Graph API
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Graph API Response Schemas
class GraphUserSchema(BaseModel):
    """User from Microsoft Graph API"""

    id: str = Field(..., description="Microsoft Graph user ID (GUID)")
    userPrincipalName: str = Field(..., description="User principal name (email)")
    displayName: Optional[str] = Field(None, description="Display name")
    accountEnabled: bool = Field(True, description="Whether account is enabled")
    department: Optional[str] = Field(None, description="Department")
    jobTitle: Optional[str] = Field(None, description="Job title")
    officeLocation: Optional[str] = Field(None, description="Office location")
    assignedLicenses: list[dict] = Field(
        default_factory=list, description="Assigned licenses"
    )


class GraphLicenseSchema(BaseModel):
    """License assignment from Graph API"""

    skuId: str = Field(..., description="SKU ID (GUID)")
    skuPartNumber: Optional[str] = Field(None, description="SKU part number")


class GraphSubscribedSkuSchema(BaseModel):
    """Subscribed SKU from Graph API"""

    skuId: str = Field(..., description="SKU ID (GUID)")
    skuPartNumber: str = Field(..., description="SKU part number")
    consumedUnits: int = Field(..., description="Number of consumed units")
    prepaidUnits: dict = Field(..., description="Prepaid units (enabled/suspended)")


class GraphUsageReportSchema(BaseModel):
    """Usage report data from Graph API"""

    userPrincipalName: Optional[str] = Field(None, description="User principal name")
    reportRefreshDate: Optional[str] = Field(None, description="Report refresh date")
    reportDate: Optional[str] = Field(None, description="Report date")
    lastActivityDate: Optional[str] = Field(None, description="Last activity date")


# Sync Request/Response Schemas
class SyncUsersRequest(BaseModel):
    """Request to sync users for a tenant"""

    force_refresh: bool = Field(
        default=False, description="Force refresh from Graph API even if cached"
    )


class SyncUsersResponse(BaseModel):
    """Response from sync_users endpoint"""

    tenant_id: str = Field(..., description="Tenant ID")
    users_synced: int = Field(..., description="Total users synced")
    users_created: int = Field(..., description="Users created")
    users_updated: int = Field(..., description="Users updated")
    duration_seconds: float = Field(..., description="Sync duration in seconds")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of sync"
    )


class SyncLicensesRequest(BaseModel):
    """Request to sync licenses for a tenant"""

    force_refresh: bool = Field(default=False, description="Force refresh from Graph")


class SyncLicensesResponse(BaseModel):
    """Response from sync_licenses endpoint"""

    tenant_id: str = Field(..., description="Tenant ID")
    licenses_synced: int = Field(..., description="Total licenses synced")
    users_processed: int = Field(..., description="Users processed")
    skus_found: int = Field(..., description="SKUs found")
    duration_seconds: float = Field(..., description="Sync duration in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncUsageRequest(BaseModel):
    """Request to sync usage reports for a tenant"""

    period: str = Field(
        default="D28",
        description="Report period (D7, D28, D90, D180)",
        pattern="^(D7|D28|D90|D180)$",
    )
    force_refresh: bool = Field(default=False, description="Force refresh from Graph")


class SyncUsageResponse(BaseModel):
    """Response from sync_usage endpoint"""

    tenant_id: str = Field(..., description="Tenant ID")
    metrics_synced: int = Field(..., description="Total metrics synced")
    users_processed: int = Field(..., description="Users processed")
    period: str = Field(..., description="Period synced")
    reports_fetched: list[str] = Field(
        default_factory=list, description="Reports fetched (email, onedrive, etc.)"
    )
    duration_seconds: float = Field(..., description="Sync duration in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Error Schemas
class GraphErrorResponse(BaseModel):
    """Error response from Graph API operations"""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    tenant_id: Optional[str] = Field(None, description="Tenant ID if applicable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
