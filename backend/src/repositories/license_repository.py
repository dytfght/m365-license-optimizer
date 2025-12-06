"""
License Repository
Handles CRUD operations for license assignments.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import AssignmentSource, LicenseAssignment, LicenseStatus
from .base import BaseRepository

logger = structlog.get_logger(__name__)


class LicenseRepository(BaseRepository[LicenseAssignment]):
    """Repository for license assignment operations"""

    def __init__(self, db: AsyncSession):
        super().__init__(LicenseAssignment, db)

    async def upsert_license(
        self,
        user_id: UUID,
        sku_id: str,
        status: LicenseStatus = LicenseStatus.ACTIVE,
        source: AssignmentSource = AssignmentSource.AUTO,
        assignment_date: Optional[datetime] = None,
    ) -> LicenseAssignment:
        """
        Insert or update a license assignment.
        Uses PostgreSQL's ON CONFLICT DO UPDATE (upsert).

        Args:
            user_id: User UUID
            sku_id: SKU ID (GUID)
            status: License status
            source: Assignment source
            assignment_date: When license was assigned

        Returns:
            LicenseAssignment instance
        """
        if assignment_date is None:
            assignment_date = datetime.utcnow()

        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = (
            pg_insert(LicenseAssignment)
            .values(
                user_id=user_id,
                sku_id=sku_id,
                status=status,
                source=source,
                assignment_date=assignment_date,
            )
            .on_conflict_do_update(
                constraint="uq_user_sku",  # UNIQUE constraint name from model
                set_={
                    "status": status,
                    "source": source,
                    "assignment_date": assignment_date,
                },
            )
            .returning(LicenseAssignment)
        )

        result = await self.session.execute(stmt)
        license_assignment = result.scalar_one()
        await self.session.commit()

        logger.debug(
            "license_upserted",
            user_id=str(user_id),
            sku_id=sku_id,
            status=status.value,
        )

        return license_assignment

    async def get_by_user(self, user_id: UUID) -> list[LicenseAssignment]:
        """
        Get all license assignments for a user.

        Args:
            user_id: User UUID

        Returns:
            List of LicenseAssignment instances
        """
        stmt = select(LicenseAssignment).where(LicenseAssignment.user_id == user_id)
        result = await self.session.execute(stmt)
        licenses = result.scalars().all()

        logger.debug(
            "licenses_fetched_for_user", user_id=str(user_id), count=len(licenses)
        )

        return list(licenses)

    async def get_by_user_and_sku(
        self, user_id: UUID, sku_id: str
    ) -> Optional[LicenseAssignment]:
        """
        Get a specific license assignment.

        Args:
            user_id: User UUID
            sku_id: SKU ID

        Returns:
            LicenseAssignment or None
        """
        stmt = select(LicenseAssignment).where(
            and_(
                LicenseAssignment.user_id == user_id,
                LicenseAssignment.sku_id == sku_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_user_and_sku(self, user_id: UUID, sku_id: str) -> None:
        """
        Delete a specific license assignment.

        Args:
            user_id: User UUID
            sku_id: SKU ID
        """
        license_assignment = await self.get_by_user_and_sku(user_id, sku_id)
        if license_assignment:
            await self.delete(license_assignment)
            logger.info("license_deleted", user_id=str(user_id), sku_id=sku_id)

    async def bulk_upsert(self, license_data: list[dict]) -> int:
        """
        Bulk upsert multiple license assignments.
        More efficient for large data sets.

        Args:
            license_data: List of dicts with user_id, sku_id, status, source

        Returns:
            Number of licenses upserted
        """
        if not license_data:
            return 0

        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = (
            pg_insert(LicenseAssignment)
            .values(license_data)
            .on_conflict_do_update(
                constraint="uq_user_sku",
                set_={
                    "status": pg_insert(LicenseAssignment).excluded.status,
                    "source": pg_insert(LicenseAssignment).excluded.source,
                    "assignment_date": pg_insert(
                        LicenseAssignment
                    ).excluded.assignment_date,
                },
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

        logger.info("licenses_bulk_upserted", count=len(license_data))

        return len(license_data)
