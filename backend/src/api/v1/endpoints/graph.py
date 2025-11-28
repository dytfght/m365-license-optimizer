"""
Microsoft Graph API endpoints for syncing users, licenses, and usage data
"""
import time
from datetime import datetime
from uuid import UUID
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.middleware import limiter
from ....models.tenant import TenantClient
from ....models.user import AssignmentSource, LicenseStatus
from ....schemas.graph import (
    SyncLicensesRequest,
    SyncLicensesResponse,
    SyncUsageRequest,
    SyncUsageResponse,
    SyncUsersRequest,
    SyncUsersResponse,
)
from ...dependencies import (
    DBSession,
    GraphServiceDep,
    LicenseRepositoryDep,
    UsageMetricsRepositoryDep,
    UserRepositoryDep,
)
from ...deps import get_current_user
from ....repositories.tenant_repository import TenantRepository

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/tenants", tags=["graph"])


async def get_tenant_with_app_reg(db: AsyncSession, tenant_id: str) -> TenantClient:
    """Get tenant with app registration or raise 404"""
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_with_app_registration(UUID(tenant_id))
    
    if not tenant:
        logger.warning("tenant_not_found", tenant_id=tenant_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found",
        )
    
    if not tenant.app_registration:
        logger.warning("app_registration_not_found", tenant_id=tenant_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant {tenant_id} has no app registration configured",
        )
    
    return tenant


@router.post(
    "/{tenant_id}/sync_users",
    response_model=SyncUsersResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync users from Microsoft Graph",
    description="Fetch all users from Microsoft Graph API and sync to database. Rate limited to 1 request per minute per tenant.",
)
@limiter.limit("1/minute")
async def sync_users(
    request: Request,
    tenant_id: str,
    body: SyncUsersRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: DBSession,
    graph_service: GraphServiceDep,
    user_repo: UserRepositoryDep,
) -> SyncUsersResponse:
    """
    Synchronize users from Microsoft Graph for a tenant.

    Steps:
    1. Verify tenant exists
    2. Fetch all users from Graph API
    3. Upsert to database (create or update)
    4. Return statistics

    Rate limited to 1 request per minute per tenant to respect Graph API limits.
    """
    start_time = time.time()

    logger.info(
        "sync_users_started", tenant_id=tenant_id, user_id=current_user["user_id"]
    )

    # Verify tenant exists with app registration
    tenant = await get_tenant_with_app_reg(db, tenant_id)

    try:
        # Fetch users from Microsoft Graph
        users_data = await graph_service.fetch_users(tenant_id)

        logger.info(
            "users_fetched_from_graph",
            tenant_id=tenant_id,
            count=len(users_data),
        )

        # Upsert users to database
        users_created = 0
        users_updated = 0

        for user_data in users_data:
            try:
                # Check if user exists
                graph_id = user_data.get("id")
                existing_user = await user_repo.get_by_graph_id(str(graph_id))

                # Upsert user
                await user_repo.upsert_user_from_graph(UUID(str(tenant.id)), user_data)

                if existing_user:
                    users_updated += 1
                else:
                    users_created += 1

            except Exception as e:
                logger.error(
                    "user_upsert_failed",
                    tenant_id=tenant_id,
                    user_graph_id=user_data.get("id"),
                    error=str(e),
                )
                # Continue with other users
                continue

        # Commit transaction
        await db.commit()

        duration = time.time() - start_time

        logger.info(
            "sync_users_completed",
            tenant_id=tenant_id,
            users_created=users_created,
            users_updated=users_updated,
            duration_seconds=duration,
        )

        return SyncUsersResponse(
            tenant_id=tenant_id,
            users_synced=len(users_data),
            users_created=users_created,
            users_updated=users_updated,
            duration_seconds=round(duration, 2),
        )

    except Exception as e:
        await db.rollback()
        logger.error(
            "sync_users_failed",
            tenant_id=tenant_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync users: {str(e)}",
        )


@router.post(
    "/{tenant_id}/sync_licenses",
    response_model=SyncLicensesResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync licenses from Microsoft Graph",
    description="Fetch license assignments from Microsoft Graph API and sync to database. Rate limited to 1 request per minute.",
)
@limiter.limit("1/minute")
async def sync_licenses(
    request: Request,
    tenant_id: str,
    body: SyncLicensesRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: DBSession,
    graph_service: GraphServiceDep,
    user_repo: UserRepositoryDep,
    license_repo: LicenseRepositoryDep,
) -> SyncLicensesResponse:
    """
    Synchronize license assignments from Microsoft Graph.

    Steps:
    1. Verify tenant exists
    2. Fetch subscribedSkus
    3. Fetch license details for all users
    4. Upsert to license_assignments table
    5. Return statistics
    """
    start_time = time.time()

    logger.info(
        "sync_licenses_started", tenant_id=tenant_id, user_id=current_user["user_id"]
    )

    # Verify tenant exists with app registration
    tenant = await get_tenant_with_app_reg(db, tenant_id)

    try:
        # Fetch subscribed SKUs
        skus = await graph_service.fetch_subscribed_skus(tenant_id)
        logger.info("subscribed_skus_fetched", tenant_id=tenant_id, count=len(skus))

        # Fetch all users for this tenant
        users = await user_repo.get_by_tenant(UUID(str(tenant.id)), limit=10000)
        logger.info("users_loaded_for_licenses", tenant_id=tenant_id, count=len(users))

        licenses_synced = 0
        users_processed = 0

        # Fetch and sync licenses for each user
        for user in users:
            try:
                # Fetch license details for this user
                license_details = await graph_service.fetch_user_license_details(
                    tenant_id, user.graph_id
                )

                # Upsert licenses
                for license_detail in license_details:
                    sku_id = license_detail.get("skuId")
                    if sku_id:
                        await license_repo.upsert_license(
                            user_id=UUID(str(user.id)),
                            sku_id=sku_id,
                            status=LicenseStatus.ACTIVE,
                            source=AssignmentSource.AUTO,
                        )
                        licenses_synced += 1

                users_processed += 1

            except Exception as e:
                logger.error(
                    "user_license_sync_failed",
                    tenant_id=tenant_id,
                    user_id=str(user.id),
                    error=str(e),
                )
                # Continue with other users
                continue

        await db.commit()

        duration = time.time() - start_time

        logger.info(
            "sync_licenses_completed",
            tenant_id=tenant_id,
            licenses_synced=licenses_synced,
            users_processed=users_processed,
            duration_seconds=duration,
        )

        return SyncLicensesResponse(
            tenant_id=tenant_id,
            licenses_synced=licenses_synced,
            users_processed=users_processed,
            skus_found=len(skus),
            duration_seconds=round(duration, 2),
        )

    except Exception as e:
        await db.rollback()
        logger.error(
            "sync_licenses_failed",
            tenant_id=tenant_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync licenses: {str(e)}",
        )


@router.post(
    "/{tenant_id}/sync_usage",
    response_model=SyncUsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync usage reports from Microsoft Graph",
    description="Fetch usage reports (email, OneDrive, SharePoint, Teams) from Microsoft Graph and sync to database. Rate limited to 1 request per minute.",
)
@limiter.limit("1/minute")
async def sync_usage(
    request: Request,
    tenant_id: str,
    body: SyncUsageRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: DBSession,
    graph_service: GraphServiceDep,
    user_repo: UserRepositoryDep,
    usage_repo: UsageMetricsRepositoryDep,
) -> SyncUsageResponse:
    """
    Synchronize usage reports from Microsoft Graph.

    Fetches and syncs:
    - Email activity (getEmailActivityUserDetail)
    - OneDrive activity (getOneDriveActivityUserDetail)
    - SharePoint activity (getSharePointActivityUserDetail)
    - Teams activity (getTeamsUserActivityUserDetail)

    Period: D7, D28, D90, D180
    """
    start_time = time.time()
    period = body.period

    logger.info(
        "sync_usage_started",
        tenant_id=tenant_id,
        period=period,
        user_id=current_user["user_id"],
    )

    # Verify tenant exists with app registration
    tenant = await get_tenant_with_app_reg(db, tenant_id)

    try:
        reports_fetched = []
        metrics_synced = 0

        # Fetch usage reports
        email_report = await graph_service.fetch_usage_report_email(tenant_id, period)
        reports_fetched.append("email")
        logger.debug("email_report_fetched", count=len(email_report))

        onedrive_report = await graph_service.fetch_usage_report_onedrive(
            tenant_id, period
        )
        reports_fetched.append("onedrive")
        logger.debug("onedrive_report_fetched", count=len(onedrive_report))

        sharepoint_report = await graph_service.fetch_usage_report_sharepoint(
            tenant_id, period
        )
        reports_fetched.append("sharepoint")
        logger.debug("sharepoint_report_fetched", count=len(sharepoint_report))

        teams_report = await graph_service.fetch_usage_report_teams(tenant_id, period)
        reports_fetched.append("teams")
        logger.debug("teams_report_fetched", count=len(teams_report))

        # Get all users for this tenant
        users = await user_repo.get_by_tenant(UUID(str(tenant.id)), limit=10000)
        user_map = {user.user_principal_name: user for user in users}

        # Process and merge reports by user
        usage_by_upn: dict[str, dict] = {}

        # Merge email activity
        for record in email_report:
            upn = record.get("User Principal Name")
            if upn:
                if upn not in usage_by_upn:
                    usage_by_upn[upn] = {}
                usage_by_upn[upn]["email_activity"] = record

        # Merge OneDrive activity
        for record in onedrive_report:
            upn = record.get("User Principal Name")
            if upn:
                if upn not in usage_by_upn:
                    usage_by_upn[upn] = {}
                usage_by_upn[upn]["onedrive_activity"] = record

        # Merge SharePoint activity
        for record in sharepoint_report:
            upn = record.get("User Principal Name")
            if upn:
                if upn not in usage_by_upn:
                    usage_by_upn[upn] = {}
                usage_by_upn[upn]["sharepoint_activity"] = record

        # Merge Teams activity
        for record in teams_report:
            upn = record.get("User Principal Name")
            if upn:
                if upn not in usage_by_upn:
                    usage_by_upn[upn] = {}
                usage_by_upn[upn]["teams_activity"] = record

        # Upsert usage metrics
        for upn, activities in usage_by_upn.items():
            user = user_map.get(upn)
            if not user:
                logger.debug("user_not_found_for_usage", upn=upn)
                continue

            try:
                # Parse report date (from any activity)
                report_date_str = (
                    activities.get("email_activity", {}).get("Report Refresh Date")
                    or activities.get("onedrive_activity", {}).get(
                        "Report Refresh Date"
                    )
                    or datetime.utcnow().strftime("%Y-%m-%d")
                )

                report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()

                # Parse last activity date
                last_activity_str = activities.get("email_activity", {}).get(
                    "Last Activity Date"
                )
                last_seen_date = None
                if last_activity_str:
                    try:
                        last_seen_date = datetime.strptime(
                            last_activity_str, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        pass

                # Upsert usage metrics
                await usage_repo.upsert_usage(
                    user_id=UUID(str(user.id)),
                    period=period,
                    report_date=report_date,
                    last_seen_date=last_seen_date,
                    email_activity=activities.get("email_activity", {}),
                    onedrive_activity=activities.get("onedrive_activity", {}),
                    sharepoint_activity=activities.get("sharepoint_activity", {}),
                    teams_activity=activities.get("teams_activity", {}),
                )

                metrics_synced += 1

            except Exception as e:
                logger.error(
                    "usage_metrics_upsert_failed",
                    tenant_id=tenant_id,
                    upn=upn,
                    error=str(e),
                )
                # Continue with other users
                continue

        await db.commit()

        duration = time.time() - start_time

        logger.info(
            "sync_usage_completed",
            tenant_id=tenant_id,
            period=period,
            metrics_synced=metrics_synced,
            duration_seconds=duration,
        )

        return SyncUsageResponse(
            tenant_id=tenant_id,
            metrics_synced=metrics_synced,
            users_processed=len(usage_by_upn),
            period=period,
            reports_fetched=reports_fetched,
            duration_seconds=round(duration, 2),
        )

    except Exception as e:
        await db.rollback()
        logger.error(
            "sync_usage_failed",
            tenant_id=tenant_id,
            period=period,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync usage: {str(e)}",
        )
