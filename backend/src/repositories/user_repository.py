"""
Repository for User and LicenseAssignment operations
"""
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.user import LicenseAssignment, User
from .base import BaseRepository

logger = structlog.get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User and LicenseAssignment operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_graph_id(self, graph_id: str) -> User | None:
        """Get user by Microsoft Graph ID"""
        result = await self.session.execute(
            select(User)
            .where(User.graph_id == graph_id)
            .options(selectinload(User.license_assignments))
        )
        return result.scalar_one_or_none()
    
    async def get_by_upn(self, upn: str, tenant_id: UUID) -> User | None:
        """Get user by UserPrincipalName within a tenant"""
        result = await self.session.execute(
            select(User)
            .where(
                User.user_principal_name == upn,
                User.tenant_client_id == tenant_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email (user_principal_name).
        Used for authentication.
        """
        result = await self.session.execute(
            select(User)
            .where(User.user_principal_name == email)
        )
        return result.scalar_one_or_none()

    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 1000,
        offset: int = 0
    ) -> list[User]:
        """Get all users for a tenant with pagination"""
        result = await self.session.execute(
            select(User)
            .where(User.tenant_client_id == tenant_id)
            .options(selectinload(User.license_assignments))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count users in a tenant"""
        from sqlalchemy import func
        
        result = await self.session.execute(
            select(func.count(User.id)).where(User.tenant_client_id == tenant_id)
        )
        return result.scalar_one()
    
    async def upsert_user(self, graph_id: str, **user_data) -> User:
        """
        Insert or update user based on graph_id.
        
        Args:
            graph_id: Microsoft Graph User ID
            **user_data: User fields to insert/update
        
        Returns:
            User entity
        """
        user = await self.get_by_graph_id(graph_id)
        
        if user:
            # Update existing
            for key, value in user_data.items():
                if hasattr(user, key) and key != "graph_id":
                    setattr(user, key, value)
            
            await self.session.flush()
            await self.session.refresh(user)
            
            logger.debug("user_updated", graph_id=graph_id)
        else:
            # Create new
            user = User(graph_id=graph_id, **user_data)
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)
            
            logger.debug("user_created", graph_id=graph_id)
        
        return user
    
    async def sync_licenses(
        self,
        user_id: UUID,
        licenses: list[dict]
    ) -> list[LicenseAssignment]:
        """
        Sync licenses for a user (replace all).
        
        Args:
            user_id: User ID
            licenses: List of license dicts with sku_id and optional metadata
        
        Returns:
            List of LicenseAssignment entities
        """
        # Delete existing licenses
        await self.session.execute(
            delete(LicenseAssignment).where(LicenseAssignment.user_id == user_id)
        )
        
        # Create new licenses
        license_entities = []
        for lic in licenses:
            lic_entity = LicenseAssignment(
                user_id=user_id,
                sku_id=lic["sku_id"],
                status=lic.get("status", "active"),
                source=lic.get("source", "manual")
            )
            self.session.add(lic_entity)
            license_entities.append(lic_entity)
        
        if license_entities:
            await self.session.flush()
        
        logger.debug(
            "user_licenses_synced",
            user_id=user_id,
            license_count=len(license_entities)
        )
        
        return license_entities
