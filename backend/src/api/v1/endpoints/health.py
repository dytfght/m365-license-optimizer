"""
Health check and version endpoints
"""
import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....core.database import get_db
from ....schemas.health import DetailedHealthCheck, HealthCheck, VersionResponse
from ...deps import get_redis

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheck, status_code=status.HTTP_200_OK)
async def basic_health_check():
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return HealthCheck(status="ok")


@router.get(
    "/api/v1/health",
    response_model=DetailedHealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="Check health of API, database, and Redis connections",
)
async def detailed_health_check(
    db: AsyncSession = Depends(get_db),
):
    """
    Detailed health check with database and Redis status.

    Args:
        db: Database session

    Returns:
        Detailed health check with service statuses
    """
    # Check database connection
    db_status = "unhealthy"
    try:
        result = await db.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_status = "ok"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))

    # Check Redis connection
    redis_status = "unhealthy"
    try:
        redis_client = await get_redis()
        if await redis_client.ping():
            redis_status = "ok"
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))

    # Overall status
    overall_status = "ok" if db_status == "ok" and redis_status == "ok" else "unhealthy"

    return DetailedHealthCheck(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        version=settings.APP_VERSION,
    )


@router.get(
    "/api/v1/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get version information",
    description="Get application version and environment information",
)
async def get_version():
    """
    Get application version and environment information.

    Returns:
        Version information
    """
    return VersionResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        lot=settings.LOT_NUMBER,
        environment=settings.ENVIRONMENT,
    )
