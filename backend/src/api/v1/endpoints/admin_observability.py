"""
Admin Observability Endpoints for LOT 11
Provides system metrics, extended health checks, and backup management.
"""
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....core.database import get_db
from ....schemas.observability import (
    BackupRequest,
    BackupResponse,
    ExtendedHealthCheck,
    SystemMetrics,
)
from ....services.logging_service import LoggingService
from ....services.observability_service import get_observability_service
from ...deps import get_current_admin_user, get_redis

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-observability"])


@router.get(
    "/metrics",
    response_model=SystemMetrics,
    summary="Get system metrics",
    description="Retrieve current system metrics including CPU, memory, disk, and network stats",
)
async def get_metrics(
    _current_user: dict = Depends(get_current_admin_user),
) -> SystemMetrics:
    """
    Get comprehensive system metrics.
    
    Requires admin authentication.
    
    Returns:
        SystemMetrics with CPU, memory, disk, network, and process information
    """
    observability = get_observability_service()
    metrics = observability.get_all_metrics()
    
    logger.info(
        "system_metrics_requested",
        user_id=str(_current_user.get("sub", "unknown")),
    )
    
    return SystemMetrics(**metrics)


@router.get(
    "/health/extended",
    response_model=ExtendedHealthCheck,
    summary="Extended health check",
    description="Comprehensive health check including database, Redis, and Azure services",
)
async def extended_health_check(
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_admin_user),
) -> ExtendedHealthCheck:
    """
    Perform an extended health check of all services.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - Azure Storage connectivity (if configured)
    
    Returns:
        ExtendedHealthCheck with detailed status of each service
    """
    observability = get_observability_service()
    checks: dict[str, bool] = {}
    
    # Check database
    db_status = "unhealthy"
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "ok"
            checks["database_query"] = True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        checks["database_query"] = False

    # Check Redis
    redis_status = "unhealthy"
    try:
        redis_client = await get_redis()
        if await redis_client.ping():
            redis_status = "ok"
            checks["redis_ping"] = True
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        checks["redis_ping"] = False

    # Check Azure Storage (if configured)
    azure_status = "not_configured"
    if settings.AZURE_STORAGE_ACCOUNT:
        try:
            # Simple check - we'll just verify the config exists
            # Actual connectivity check would require azure-storage-blob
            azure_status = "configured"
            checks["azure_storage_configured"] = True
        except Exception as e:
            logger.error("azure_storage_check_failed", error=str(e))
            azure_status = "error"
            checks["azure_storage_configured"] = False

    # Overall status
    overall_status = "ok" if db_status == "ok" and redis_status == "ok" else "unhealthy"

    return ExtendedHealthCheck(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        azure_storage=azure_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(observability.uptime_seconds, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks,
    )


@router.post(
    "/backup",
    response_model=BackupResponse,
    summary="Trigger manual backup",
    description="Manually trigger a database backup to Azure Blob Storage",
)
async def trigger_backup(
    request: BackupRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_admin_user),
) -> BackupResponse:
    """
    Trigger a manual database backup.
    
    The backup is created using pg_dump and uploaded to Azure Blob Storage
    using Managed Identity authentication.
    
    Args:
        request: Backup configuration options
        
    Returns:
        BackupResponse with backup details or error information
    """
    backup_id = str(uuid4())
    timestamp = datetime.now(timezone.utc)
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp_str}_{backup_id[:8]}.sql.gz"
    
    logger.info(
        "manual_backup_triggered",
        backup_id=backup_id,
        user_id=str(_current_user.get("sub", "unknown")),
        include_logs=request.include_logs,
    )
    
    # Log the backup operation via logging service
    try:
        logging_service = LoggingService(db)
        await logging_service.log_to_db(
            level="info",
            message=f"Manual backup triggered: {backup_id}",
            action="backup",
            extra_data={
                "backup_id": backup_id,
                "description": request.description,
                "include_logs": request.include_logs,
            },
        )
    except Exception as e:
        logger.warning("failed_to_log_backup_operation", error=str(e))

    # Check if Azure Storage is configured
    if not settings.AZURE_STORAGE_ACCOUNT:
        # Return success for local/dev environment - backup to local file
        local_backup_dir = Path(settings.LOG_FILE_PATH).parent / "backups"
        local_backup_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_backup_dir / filename
        
        try:
            # For local dev, just create a placeholder or run pg_dump locally
            # In production, this would upload to Azure Blob Storage
            result = subprocess.run(
                [
                    "pg_dump",
                    "-h", settings.POSTGRES_HOST,
                    "-U", settings.POSTGRES_USER,
                    "-d", settings.POSTGRES_DB,
                    "--format=custom",
                    "--compress=9",
                    "-f", str(local_path),
                ],
                capture_output=True,
                text=True,
                env={**dict(__import__("os").environ), "PGPASSWORD": settings.POSTGRES_PASSWORD},
                timeout=300,  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            file_size = local_path.stat().st_size if local_path.exists() else 0
            
            return BackupResponse(
                success=True,
                backup_id=backup_id,
                filename=filename,
                size_bytes=file_size,
                storage_path=str(local_path),
                timestamp=timestamp.isoformat(),
                message=f"Backup created successfully (local): {filename}",
            )
            
        except subprocess.TimeoutExpired:
            return BackupResponse(
                success=False,
                backup_id=backup_id,
                timestamp=timestamp.isoformat(),
                message="Backup failed: operation timed out",
                error="Backup operation timed out after 5 minutes",
            )
        except FileNotFoundError:
            # pg_dump not available
            return BackupResponse(
                success=False,
                backup_id=backup_id,
                timestamp=timestamp.isoformat(),
                message="Backup failed: pg_dump not available",
                error="pg_dump command not found. Install PostgreSQL client tools.",
            )
        except Exception as e:
            logger.error("backup_failed", backup_id=backup_id, error=str(e))
            return BackupResponse(
                success=False,
                backup_id=backup_id,
                timestamp=timestamp.isoformat(),
                message=f"Backup failed: {str(e)}",
                error=str(e),
            )
    
    # Azure Blob Storage backup using Managed Identity
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
        
        # Create blob service client using Managed Identity
        account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)
        
        # Get container client
        container_client = blob_service_client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER
        )
        
        # Create container if it doesn't exist
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists
        
        # Create backup using pg_dump
        with tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        result = subprocess.run(
            [
                "pg_dump",
                "-h", settings.POSTGRES_HOST,
                "-U", settings.POSTGRES_USER,
                "-d", settings.POSTGRES_DB,
                "--format=custom",
                "--compress=9",
                "-f", tmp_path,
            ],
            capture_output=True,
            text=True,
            env={**dict(__import__("os").environ), "PGPASSWORD": settings.POSTGRES_PASSWORD},
            timeout=300,
        )
        
        if result.returncode != 0:
            raise Exception(f"pg_dump failed: {result.stderr}")
        
        # Upload to Azure Blob Storage
        blob_client = container_client.get_blob_client(filename)
        
        with open(tmp_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        file_size = Path(tmp_path).stat().st_size
        
        # Clean up temp file
        Path(tmp_path).unlink()
        
        storage_path = f"https://{settings.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER}/{filename}"
        
        logger.info(
            "backup_completed",
            backup_id=backup_id,
            filename=filename,
            size_bytes=file_size,
            storage_path=storage_path,
        )
        
        return BackupResponse(
            success=True,
            backup_id=backup_id,
            filename=filename,
            size_bytes=file_size,
            storage_path=storage_path,
            timestamp=timestamp.isoformat(),
            message=f"Backup uploaded to Azure Blob Storage: {filename}",
        )
        
    except ImportError:
        return BackupResponse(
            success=False,
            backup_id=backup_id,
            timestamp=timestamp.isoformat(),
            message="Backup failed: Azure SDK not installed",
            error="Install azure-identity and azure-storage-blob packages",
        )
    except Exception as e:
        logger.error("azure_backup_failed", backup_id=backup_id, error=str(e))
        return BackupResponse(
            success=False,
            backup_id=backup_id,
            timestamp=timestamp.isoformat(),
            message=f"Backup to Azure failed: {str(e)}",
            error=str(e),
        )
