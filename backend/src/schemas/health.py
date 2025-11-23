"""
Pydantic schemas for health check and version endpoints
"""
from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    """Basic health check response"""

    status: str = Field(..., description="Health status (ok/unhealthy)")


class DetailedHealthCheck(BaseModel):
    """Detailed health check with service statuses"""

    status: str = Field(..., description="Overall health status")
    database: str = Field(..., description="Database connection status")
    redis: str = Field(..., description="Redis connection status")
    version: str = Field(..., description="Application version")


class VersionResponse(BaseModel):
    """Version information response"""

    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    lot: int = Field(..., description="Current lot number")
    environment: str = Field(
        ..., description="Environment (development/test/production)"
    )
