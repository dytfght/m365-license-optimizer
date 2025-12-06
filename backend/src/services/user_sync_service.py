"""
Service for syncing users from Microsoft Graph
"""
from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..integrations.graph import GraphAuthService, GraphClient
from ..repositories.tenant_repository import TenantRepository
from ..repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class UserSyncService:
    """Service for synchronizing users from Microsoft Graph"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.tenant_repo = TenantRepository(session)
        self.user_repo = UserRepository(session)
        self.graph_auth = GraphAuthService()

    async def sync_users(self, tenant_id: UUID) -> dict:
        """
        Sync all users from Microsoft Graph for a tenant.

        Args:
            tenant_id: Internal tenant ID

        Returns:
            dict with sync statistics
        """
        start_time = datetime.now(timezone.utc)

        # Get tenant with app registration
        tenant = await self.tenant_repo.get_with_app_registration(tenant_id)
        if not tenant or not tenant.app_registration:
            raise ValueError(f"Tenant {tenant_id} or app registration not found")

        app_reg = tenant.app_registration

        try:
            # Get Graph API token
            if not app_reg.client_secret_encrypted:
                raise ValueError(f"Tenant {tenant_id} has no client secret configured")

            token = await self.graph_auth.get_token(
                tenant.tenant_id, app_reg.client_id, app_reg.client_secret_encrypted
            )

            # Create Graph client
            graph_client = GraphClient(token)

            try:
                # Fetch users from Graph
                logger.info("user_sync_started", tenant_id=tenant_id)

                users_data = await graph_client.get_users()

                synced_count = 0
                created_count = 0
                updated_count = 0

                for user_data in users_data:
                    graph_id = user_data["id"]

                    # Check if user exists
                    existing_user = await self.user_repo.get_by_graph_id(graph_id)
                    is_new = existing_user is None

                    # Prepare user data
                    user_fields = {
                        "tenant_client_id": tenant_id,
                        "user_principal_name": user_data.get("userPrincipalName", ""),
                        "display_name": user_data.get("displayName"),
                        "account_enabled": user_data.get("accountEnabled", True),
                        "department": user_data.get("department"),
                        "job_title": user_data.get("jobTitle"),
                        "office_location": user_data.get("officeLocation"),
                    }

                    # Upsert user
                    user = await self.user_repo.upsert_user(graph_id, **user_fields)

                    # Sync licenses
                    assigned_licenses = user_data.get("assignedLicenses", [])
                    licenses = [
                        {"sku_id": lic["skuId"], "status": "active", "source": "manual"}
                        for lic in assigned_licenses
                    ]

                    await self.user_repo.sync_licenses(UUID(str(user.id)), licenses)

                    synced_count += 1
                    if is_new:
                        created_count += 1
                    else:
                        updated_count += 1

                # Commit transaction
                await self.session.commit()

                duration = (datetime.now(timezone.utc) - start_time).total_seconds()

                logger.info(
                    "user_sync_completed",
                    tenant_id=tenant_id,
                    synced=synced_count,
                    created=created_count,
                    updated=updated_count,
                    duration_seconds=duration,
                )

                return {
                    "synced": synced_count,
                    "created": created_count,
                    "updated": updated_count,
                    "duration_seconds": duration,
                }

            finally:
                await graph_client.close()

        finally:
            await self.graph_auth.close()
