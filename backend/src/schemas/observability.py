"""
Pydantic schemas for observability and metrics endpoints (LOT 11)
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CpuMetrics(BaseModel):
    """CPU usage metrics"""

    percent: float = Field(..., description="CPU usage percentage")
    count_physical: Optional[int] = Field(None, description="Physical CPU cores")
    count_logical: Optional[int] = Field(None, description="Logical CPU cores")
    frequency_mhz: Optional[float] = Field(None, description="Current CPU frequency in MHz")
    frequency_max_mhz: Optional[float] = Field(None, description="Max CPU frequency in MHz")
    error: Optional[str] = Field(None, description="Error message if metrics unavailable")


class MemoryMetrics(BaseModel):
    """Memory usage metrics"""

    total_bytes: Optional[int] = Field(None, description="Total memory in bytes")
    available_bytes: Optional[int] = Field(None, description="Available memory in bytes")
    used_bytes: Optional[int] = Field(None, description="Used memory in bytes")
    percent: Optional[float] = Field(None, description="Memory usage percentage")
    total_gb: Optional[float] = Field(None, description="Total memory in GB")
    available_gb: Optional[float] = Field(None, description="Available memory in GB")
    used_gb: Optional[float] = Field(None, description="Used memory in GB")
    error: Optional[str] = Field(None, description="Error message if metrics unavailable")


class DiskMetrics(BaseModel):
    """Disk usage metrics"""

    path: str = Field(..., description="Disk path checked")
    total_bytes: Optional[int] = Field(None, description="Total disk space in bytes")
    used_bytes: Optional[int] = Field(None, description="Used disk space in bytes")
    free_bytes: Optional[int] = Field(None, description="Free disk space in bytes")
    percent: Optional[float] = Field(None, description="Disk usage percentage")
    total_gb: Optional[float] = Field(None, description="Total disk space in GB")
    used_gb: Optional[float] = Field(None, description="Used disk space in GB")
    free_gb: Optional[float] = Field(None, description="Free disk space in GB")
    error: Optional[str] = Field(None, description="Error message if metrics unavailable")


class NetworkMetrics(BaseModel):
    """Network I/O metrics"""

    bytes_sent: Optional[int] = Field(None, description="Total bytes sent")
    bytes_recv: Optional[int] = Field(None, description="Total bytes received")
    packets_sent: Optional[int] = Field(None, description="Total packets sent")
    packets_recv: Optional[int] = Field(None, description="Total packets received")
    bytes_sent_mb: Optional[float] = Field(None, description="Bytes sent in MB")
    bytes_recv_mb: Optional[float] = Field(None, description="Bytes received in MB")
    error: Optional[str] = Field(None, description="Error message if metrics unavailable")


class ProcessMetrics(BaseModel):
    """Current process metrics"""

    pid: Optional[int] = Field(None, description="Process ID")
    memory_rss_bytes: Optional[int] = Field(None, description="Resident set size in bytes")
    memory_rss_mb: Optional[float] = Field(None, description="Resident set size in MB")
    memory_vms_bytes: Optional[int] = Field(None, description="Virtual memory size in bytes")
    memory_vms_mb: Optional[float] = Field(None, description="Virtual memory size in MB")
    cpu_percent: Optional[float] = Field(None, description="CPU usage percentage")
    num_threads: Optional[int] = Field(None, description="Number of threads")
    create_time: Optional[str] = Field(None, description="Process creation time")
    error: Optional[str] = Field(None, description="Error message if metrics unavailable")


class SystemInfo(BaseModel):
    """System information"""

    platform: str = Field(..., description="Operating system name")
    platform_release: str = Field(..., description="OS release version")
    platform_version: str = Field(..., description="OS version details")
    architecture: str = Field(..., description="CPU architecture")
    hostname: str = Field(..., description="Machine hostname")
    python_version: str = Field(..., description="Python version")
    psutil_available: bool = Field(..., description="Whether psutil is available")


class SystemMetrics(BaseModel):
    """Complete system metrics response"""

    timestamp: str = Field(..., description="Metrics collection timestamp (ISO 8601)")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    system: SystemInfo = Field(..., description="System information")
    cpu: dict[str, Any] = Field(..., description="CPU metrics")
    memory: dict[str, Any] = Field(..., description="Memory metrics")
    disk: dict[str, Any] = Field(..., description="Disk metrics")
    network: dict[str, Any] = Field(..., description="Network metrics")
    process: dict[str, Any] = Field(..., description="Process metrics")


class ExtendedHealthCheck(BaseModel):
    """Extended health check with all service statuses"""

    status: str = Field(..., description="Overall health status")
    database: str = Field(..., description="Database connection status")
    redis: str = Field(..., description="Redis connection status")
    azure_storage: str = Field(default="not_configured", description="Azure Storage status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment (development/production)")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    timestamp: str = Field(..., description="Health check timestamp")
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual check results")


class BackupRequest(BaseModel):
    """Request to trigger a manual backup"""

    include_logs: bool = Field(default=False, description="Include audit logs in backup")
    description: Optional[str] = Field(None, description="Optional backup description")


class BackupResponse(BaseModel):
    """Response from backup operation"""

    success: bool = Field(..., description="Whether backup was successful")
    backup_id: Optional[str] = Field(default=None, description="Unique backup identifier")
    filename: Optional[str] = Field(default=None, description="Backup filename")
    size_bytes: Optional[int] = Field(default=None, description="Backup file size in bytes")
    storage_path: Optional[str] = Field(default=None, description="Storage path/URL")
    timestamp: str = Field(..., description="Backup timestamp")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(default=None, description="Error message if backup failed")


class BackupInfo(BaseModel):
    """Information about an existing backup"""

    backup_id: str = Field(..., description="Unique backup identifier")
    filename: str = Field(..., description="Backup filename")
    size_bytes: int = Field(..., description="Backup file size in bytes")
    created_at: datetime = Field(..., description="Backup creation time")
    description: Optional[str] = Field(None, description="Backup description")
    storage_path: str = Field(..., description="Storage path/URL")


class BackupListResponse(BaseModel):
    """List of backups"""

    backups: list[BackupInfo] = Field(default_factory=list, description="List of backups")
    total_count: int = Field(..., description="Total number of backups")
    total_size_bytes: int = Field(..., description="Total size of all backups")
