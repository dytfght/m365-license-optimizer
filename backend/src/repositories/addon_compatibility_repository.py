"""
Addon Compatibility Repository
Handles database operations for addon compatibility mappings
"""
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.addon_compatibility import AddonCompatibility
from .base import BaseRepository


class AddonCompatibilityRepository(BaseRepository[AddonCompatibility]):
    """Repository for addon compatibility operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(AddonCompatibility, session)

    async def get_by_addon_sku(self, addon_sku_id: str) -> List[AddonCompatibility]:
        """Get all compatibility mappings for a specific add-on SKU"""
        result = await self.session.execute(
            select(self.model).where(self.model.addon_sku_id == addon_sku_id)
        )
        return list(result.scalars().all())

    async def get_by_base_sku(self, base_sku_id: str) -> List[AddonCompatibility]:
        """Get all compatibility mappings for a specific base SKU"""
        result = await self.session.execute(
            select(self.model).where(self.model.base_sku_id == base_sku_id)
        )
        return list(result.scalars().all())

    async def get_by_service_type(self, service_type: str) -> List[AddonCompatibility]:
        """Get all compatibility mappings for a specific service type"""
        result = await self.session.execute(
            select(self.model).where(self.model.service_type == service_type)
        )
        return list(result.scalars().all())

    async def get_by_addon_category(
        self, addon_category: str
    ) -> List[AddonCompatibility]:
        """Get all compatibility mappings for a specific add-on category"""
        result = await self.session.execute(
            select(self.model).where(self.model.addon_category == addon_category)
        )
        return list(result.scalars().all())

    async def get_compatible_addons(
        self,
        base_sku_id: str,
        service_type: Optional[str] = None,
        addon_category: Optional[str] = None,
        active_only: bool = True,
    ) -> List[AddonCompatibility]:
        """Get all compatible add-ons for a base SKU with optional filters"""
        query = select(self.model).where(self.model.base_sku_id == base_sku_id)

        if service_type:
            query = query.where(self.model.service_type == service_type)

        if addon_category:
            query = query.where(self.model.addon_category == addon_category)

        if active_only:
            query = query.where(self.model.is_active.is_(True))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_specific_mapping(
        self, addon_sku_id: str, base_sku_id: str
    ) -> Optional[AddonCompatibility]:
        """Get specific mapping between add-on and base SKU"""
        result = await self.session.execute(
            select(self.model).where(
                and_(
                    self.model.addon_sku_id == addon_sku_id,
                    self.model.base_sku_id == base_sku_id,
                    self.model.is_active.is_(True)  # Only active mappings
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_active_mappings(self) -> List[AddonCompatibility]:
        """Get all active compatibility mappings"""
        result = await self.session.execute(
            select(self.model).where(self.model.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def validate_compatibility(
        self, addon_sku_id: str, base_sku_id: str, quantity: int
    ) -> bool:
        """Validate if add-on is compatible with base SKU at given quantity"""
        mapping = await self.get_specific_mapping(addon_sku_id, base_sku_id)

        if not mapping:
            return False

        return mapping.is_compatible(base_sku_id, quantity) and mapping.is_available()

    async def bulk_create(self, mappings: List[dict]) -> List[AddonCompatibility]:
        """Create multiple compatibility mappings in bulk"""
        created_mappings = []

        for mapping_data in mappings:
            mapping = self.model(**mapping_data)
            self.session.add(mapping)
            created_mappings.append(mapping)

        await self.session.flush()

        # Refresh all created mappings
        for mapping in created_mappings:
            await self.session.refresh(mapping)

        return created_mappings

    async def update_by_sku_mapping(
        self, addon_sku_id: str, base_sku_id: str, **kwargs
    ) -> Optional[AddonCompatibility]:
        """Update a specific mapping by add-on and base SKU IDs"""
        mapping = await self.get_specific_mapping(addon_sku_id, base_sku_id)

        if mapping:
            return await self.update(mapping, **kwargs)

        return None

    async def deactivate_mapping(
        self, addon_sku_id: str, base_sku_id: str
    ) -> Optional[AddonCompatibility]:
        """Deactivate a specific compatibility mapping"""
        return await self.update_by_sku_mapping(
            addon_sku_id, base_sku_id, is_active=False
        )

    async def activate_mapping(
        self, addon_sku_id: str, base_sku_id: str
    ) -> Optional[AddonCompatibility]:
        """Activate a specific compatibility mapping"""
        return await self.update_by_sku_mapping(
            addon_sku_id, base_sku_id, is_active=True
        )
