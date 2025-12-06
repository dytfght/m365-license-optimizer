"""
Pydantic schemas for report generation and management
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReportCreateRequest(BaseModel):
    """Request model for creating a report"""

    analysis_id: UUID = Field(
        ..., description="ID of the analysis to generate report for"
    )

    class Config:
        json_encoders = {UUID: str}


class ReportResponse(BaseModel):
    """Response model for a report"""

    id: UUID = Field(..., description="Report ID")
    analysis_id: UUID = Field(..., description="Analysis ID")
    tenant_client_id: UUID = Field(..., description="Tenant client ID")

    report_type: str = Field(..., description="Type of report (PDF or EXCEL)")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")

    report_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Report metadata (KPIs, stats)"
    )
    generated_by: str = Field(..., description="Email of user who generated the report")

    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(
        None, description="Expiration timestamp for cleanup"
    )

    # Computed fields
    download_url: Optional[str] = Field(
        default=None, description="URL to download the report file"
    )

    class Config:
        from_attributes = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}

    @classmethod
    def from_report(cls, report) -> "ReportResponse":
        """Create response from Report model, handling field mapping"""
        return cls(
            id=report.id,
            analysis_id=report.analysis_id,
            tenant_client_id=report.tenant_client_id,
            report_type=report.report_type,
            file_name=report.file_name,
            file_size=report.file_size_bytes,  # Map file_size_bytes to file_size
            mime_type=report.mime_type,
            report_metadata=report.report_metadata,
            generated_by=report.generated_by,
            created_at=report.created_at,
            expires_at=report.expires_at,
        )


class ReportListResponse(BaseModel):
    """Response model for list of reports"""

    reports: List[ReportResponse] = Field(..., description="List of reports")
    total: int = Field(..., description="Total number of reports")
    limit: int = Field(..., description="Maximum number of reports returned")
    offset: int = Field(..., description="Number of reports skipped")

    class Config:
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}


class ReportDownloadResponse(BaseModel):
    """Response model for report download information"""

    report_id: UUID = Field(..., description="Report ID")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    download_url: str = Field(..., description="URL to download the report file")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    class Config:
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}


class ReportMetadata(BaseModel):
    """Metadata structure for reports"""

    generated_at: datetime = Field(..., description="When the report was generated")
    report_version: str = Field("1.0", description="Report format version")
    tenant_name: str = Field(..., description="Name of the tenant")
    period_start: str = Field(..., description="Analysis period start date")
    period_end: str = Field(..., description="Analysis period end date")

    # KPIs
    total_users: int = Field(..., description="Total number of users analyzed")
    current_monthly_cost: float = Field(..., description="Current monthly cost in EUR")
    target_monthly_cost: float = Field(..., description="Target monthly cost in EUR")
    monthly_savings: float = Field(..., description="Monthly savings in EUR")
    annual_savings: float = Field(..., description="Annual savings in EUR")
    savings_percentage: float = Field(..., description="Savings percentage")

    # Recommendations
    recommendations_count: int = Field(
        ..., description="Total number of recommendations"
    )
    top_recommendations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top 3 recommendations by savings"
    )

    # Charts data
    license_distribution: List[Dict[str, Any]] = Field(
        default_factory=list, description="License distribution data for charts"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ReportFilter(BaseModel):
    """Filter criteria for reports"""

    report_type: Optional[str] = Field(
        None, description="Filter by report type (PDF/EXCEL)"
    )
    date_from: Optional[datetime] = Field(
        None, description="Reports created after this date"
    )
    date_to: Optional[datetime] = Field(
        None, description="Reports created before this date"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
