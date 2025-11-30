"""
Analytics schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.analytics import MetricType, SnapshotType


# Base schemas
class AnalyticsMetricBase(BaseModel):
    """Base schema for analytics metrics"""

    metric_type: MetricType = Field(..., description="Type of metric")
    metric_name: str = Field(
        ..., description="Human-readable metric name", max_length=255
    )
    value: str = Field(
        ...,
        description="Metric value (can be number, percentage, etc.)",
        max_length=255,
    )
    period_start: datetime = Field(..., description="Start of the measurement period")
    period_end: datetime = Field(..., description="End of the measurement period")
    unit: Optional[str] = Field(
        None, description="Unit of measurement (%, users, GB, etc.)", max_length=50
    )
    context: Optional[dict] = Field(
        None, description="Additional context data for the metric"
    )


class AnalyticsSnapshotBase(BaseModel):
    """Base schema for analytics snapshots"""

    snapshot_type: SnapshotType = Field(..., description="Type of snapshot")
    snapshot_date: datetime = Field(..., description="Date when the snapshot was taken")
    snapshot_data: dict = Field(..., description="Snapshot data in JSON format")
    snapshot_metadata: Optional[dict] = Field(
        None, description="Additional metadata about the snapshot"
    )
    data_hash: Optional[str] = Field(
        None,
        description="SHA-256 hash of the snapshot data for integrity checking",
        max_length=64,
    )


# Request schemas
class AnalyticsMetricCreate(AnalyticsMetricBase):
    """Schema for creating an analytics metric"""

    tenant_client_id: UUID = Field(..., description="Tenant client ID")


class AnalyticsSnapshotCreate(AnalyticsSnapshotBase):
    """Schema for creating an analytics snapshot"""

    tenant_client_id: UUID = Field(..., description="Tenant client ID")


class AnalyticsMetricUpdate(BaseModel):
    """Schema for updating an analytics metric"""

    metric_type: Optional[MetricType] = Field(None, description="Type of metric")
    metric_name: Optional[str] = Field(
        None, description="Human-readable metric name", max_length=255
    )
    value: Optional[str] = Field(
        None,
        description="Metric value (can be number, percentage, etc.)",
        max_length=255,
    )
    period_start: Optional[datetime] = Field(
        None, description="Start of the measurement period"
    )
    period_end: Optional[datetime] = Field(
        None, description="End of the measurement period"
    )
    unit: Optional[str] = Field(
        None, description="Unit of measurement (%, users, GB, etc.)", max_length=50
    )
    context: Optional[dict] = Field(
        None, description="Additional context data for the metric"
    )


class AnalyticsSnapshotUpdate(BaseModel):
    """Schema for updating an analytics snapshot"""

    snapshot_type: Optional[SnapshotType] = Field(None, description="Type of snapshot")
    snapshot_date: Optional[datetime] = Field(
        None, description="Date when the snapshot was taken"
    )
    snapshot_data: Optional[dict] = Field(
        None, description="Snapshot data in JSON format"
    )
    snapshot_metadata: Optional[dict] = Field(
        None, description="Additional metadata about the snapshot"
    )
    data_hash: Optional[str] = Field(
        None,
        description="SHA-256 hash of the snapshot data for integrity checking",
        max_length=64,
    )


# Response schemas
class AnalyticsMetricResponse(AnalyticsMetricBase):
    """Schema for analytics metric response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Metric ID")
    tenant_client_id: UUID = Field(..., description="Tenant client ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class AnalyticsSnapshotResponse(AnalyticsSnapshotBase):
    """Schema for analytics snapshot response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Snapshot ID")
    tenant_client_id: UUID = Field(..., description="Tenant client ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


# List response schemas
class AnalyticsMetricListResponse(BaseModel):
    """Schema for analytics metric list response"""

    metrics: list[AnalyticsMetricResponse] = Field(
        ..., description="List of analytics metrics"
    )
    total: int = Field(..., description="Total number of metrics")
    page: int = Field(1, description="Current page")
    page_size: int = Field(50, description="Page size")


class AnalyticsSnapshotListResponse(BaseModel):
    """Schema for analytics snapshot list response"""

    snapshots: list[AnalyticsSnapshotResponse] = Field(
        ..., description="List of analytics snapshots"
    )
    total: int = Field(..., description="Total number of snapshots")
    page: int = Field(1, description="Current page")
    page_size: int = Field(50, description="Page size")


# Filter schemas
class AnalyticsMetricFilter(BaseModel):
    """Schema for filtering analytics metrics"""

    tenant_client_id: Optional[UUID] = Field(
        None, description="Filter by tenant client ID"
    )
    metric_type: Optional[MetricType] = Field(None, description="Filter by metric type")
    period_start: Optional[datetime] = Field(
        None, description="Filter by period start date (greater than or equal)"
    )
    period_end: Optional[datetime] = Field(
        None, description="Filter by period end date (less than or equal)"
    )
    metric_name: Optional[str] = Field(
        None, description="Filter by metric name (partial match)"
    )


class AnalyticsSnapshotFilter(BaseModel):
    """Schema for filtering analytics snapshots"""

    tenant_client_id: Optional[UUID] = Field(
        None, description="Filter by tenant client ID"
    )
    snapshot_type: Optional[SnapshotType] = Field(
        None, description="Filter by snapshot type"
    )
    snapshot_date: Optional[datetime] = Field(
        None, description="Filter by snapshot date (greater than or equal)"
    )
    snapshot_date_to: Optional[datetime] = Field(
        None, description="Filter by snapshot date (less than or equal)"
    )


# KPI schemas
class KPIResponse(BaseModel):
    """Schema for KPI response"""

    metric_type: MetricType = Field(..., description="Type of metric")
    metric_name: str = Field(..., description="Human-readable metric name")
    value: str = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    period_start: datetime = Field(..., description="Start of the measurement period")
    period_end: datetime = Field(..., description="End of the measurement period")
    trend: Optional[str] = Field(None, description="Trend direction (up, down, stable)")
    change_percentage: Optional[float] = Field(
        None, description="Percentage change from previous period"
    )


class DashboardKPIsResponse(BaseModel):
    """Schema for dashboard KPIs response"""

    kpis: list[KPIResponse] = Field(..., description="List of KPIs for the dashboard")
    period_start: datetime = Field(..., description="Start of the measurement period")
    period_end: datetime = Field(..., description="End of the measurement period")
    generated_at: datetime = Field(..., description="When the KPIs were generated")


# Analytics summary schema
class AnalyticsSummaryResponse(BaseModel):
    """Schema for analytics summary response"""

    tenant_client_id: UUID = Field(..., description="Tenant client ID")
    total_metrics: int = Field(..., description="Total number of metrics")
    total_snapshots: int = Field(..., description="Total number of snapshots")
    metric_types: list[MetricType] = Field(..., description="Available metric types")
    snapshot_types: list[SnapshotType] = Field(
        ..., description="Available snapshot types"
    )
    date_range: dict[str, datetime] = Field(
        ..., description="Date range of available data"
    )
    last_updated: datetime = Field(
        ..., description="When the analytics were last updated"
    )
