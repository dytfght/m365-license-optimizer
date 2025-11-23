"""
Repository for Tenant operations
"""
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.tenant import OnboardingStatus, TenantAppRegistration, TenantClient
from .base import BaseRepository

logger = structlog.get_logger(__name__)


class TenantRepository(BaseRepository[TenantClient]):
    """Repository for TenantClient and TenantAppRegistration operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(TenantClient, session)

    async def get_by_tenant_id(self, tenant_id: str) -> TenantClient | None:
        """Get tenant by Azure AD tenant ID"""
        result = await self.session.execute(
            select(TenantClient)
            .where(TenantClient.tenant_id == tenant_id)
            .options(selectinload(TenantClient.app_registration))
        )
        return result.scalar_one_or_none()

    async def get_with_app_registration(self, id: UUID) -> TenantClient | None:
        """Get tenant with app registration eagerly loaded"""
        result = await self.session.execute(
            select(TenantClient)
            .where(TenantClient.id == id)
            .options(selectinload(TenantClient.app_registration))
        )
        return result.scalar_one_or_none()

    async def get_active_tenants(self) -> list[TenantClient]:
        """Get all active tenants"""
        result = await self.session.execute(
            select(TenantClient)
            .where(TenantClient.onboarding_status == OnboardingStatus.ACTIVE)
            .options(selectinload(TenantClient.app_registration))
        )
        return list(result.scalars().all())

    async def create_with_app_registration(
        self, tenant_data: dict, app_reg_data: dict
    ) -> TenantClient:
        """
        Create tenant with app registration in a single transaction.

        Args:
            tenant_data: TenantClient fields
            app_reg_data: TenantAppRegistration fields

        Returns:
            Created TenantClient with app_registration
        """
        # Create tenant
        tenant = TenantClient(**tenant_data)
        self.session.add(tenant)
        await self.session.flush()

        # Create app registration
        app_reg = TenantAppRegistration(tenant_client_id=tenant.id, **app_reg_data)
        self.session.add(app_reg)
        await self.session.flush()

        # Refresh to load relationship
        await self.session.refresh(tenant, ["app_registration"])

        logger.info(
            "tenant_with_app_registration_created",
            tenant_id=tenant.id,
            tenant_name=tenant.name,
        )

        return tenant

    async def update_app_registration(
        self, tenant_id: UUID, **kwargs
    ) -> TenantAppRegistration:
        """Update app registration for a tenant"""
        result = await self.session.execute(
            select(TenantAppRegistration).where(
                TenantAppRegistration.tenant_client_id == tenant_id
            )
        )
        app_reg = result.scalar_one_or_none()

        if not app_reg:
            raise ValueError(f"App registration not found for tenant {tenant_id}")

        for key, value in kwargs.items():
            if hasattr(app_reg, key):
                setattr(app_reg, key, value)

        await self.session.flush()
        await self.session.refresh(app_reg)

        logger.info(
            "app_registration_updated", tenant_id=tenant_id, fields=list(kwargs.keys())
        )

        return app_reg
