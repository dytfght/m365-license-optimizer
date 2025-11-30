"""
SKU Mapping Service
Handles mapping between Graph API SKUs and Partner Center SKUs
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.addon_compatibility import AddonCompatibility
from ..models.microsoft_product import MicrosoftProduct
from ..repositories.addon_compatibility_repository import AddonCompatibilityRepository
from ..repositories.product_repository import ProductRepository

logger = structlog.get_logger(__name__)


class SkuMappingService:
    """Service for managing SKU mappings between Graph API and Partner Center"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repo = ProductRepository(session)
        self.addon_repo = AddonCompatibilityRepository(session)

    async def get_graph_sku_info(self, sku_id: str) -> Optional[Dict]:
        """Get SKU information from Graph API perspective"""
        # This would typically call Graph API, but for now we'll use mock data
        # In a real implementation, this would call Microsoft Graph API
        graph_sku_mapping = {
            "O365_BUSINESS_PREMIUM": {
                "sku_id": "O365_BUSINESS_PREMIUM",
                "name": "Microsoft 365 Business Premium",
                "service_plans": ["SHAREPOINTWAC", "SWAY", "YAMMER_ENTERPRISE"],
                "category": "Business",
            },
            "ENTERPRISEPACK": {
                "sku_id": "ENTERPRISEPACK",
                "name": "Office 365 E3",
                "service_plans": ["SHAREPOINTWAC", "SWAY", "YAMMER_ENTERPRISE"],
                "category": "Enterprise",
            },
            "SPE_E3": {
                "sku_id": "SPE_E3",
                "name": "Microsoft 365 E3",
                "service_plans": ["SHAREPOINTWAC", "SWAY", "YAMMER_ENTERPRISE"],
                "category": "Enterprise",
            },
            "SPE_E5": {
                "sku_id": "SPE_E5",
                "name": "Microsoft 365 E5",
                "service_plans": ["SHAREPOINTWAC", "SWAY", "YAMMER_ENTERPRISE"],
                "category": "Enterprise",
            },
        }

        return graph_sku_mapping.get(sku_id)

    async def get_partner_center_sku(
        self, graph_sku_id: str
    ) -> Optional[MicrosoftProduct]:
        """Get Partner Center SKU information for a Graph SKU"""
        # For now, we'll use a simple mapping based on SKU names
        # In a real implementation, this would use a proper mapping table
        sku_mapping = {
            "O365_BUSINESS_PREMIUM": "CFQ7TTC0LF8S:0001",
            "ENTERPRISEPACK": "CFQ7TTC0LF8S:0002",
            "SPE_E3": "CFQ7TTC0LH0B:0001",
            "SPE_E5": "CFQ7TTC0LH0B:0002",
        }

        partner_sku_id = sku_mapping.get(graph_sku_id)
        if not partner_sku_id:
            return None

        product_id, sku_id = partner_sku_id.split(":")
        return await self.product_repo.get_by_product_and_sku(product_id, sku_id)

    async def map_graph_to_partner_center(
        self, graph_sku_ids: List[str]
    ) -> Dict[str, Optional[MicrosoftProduct]]:
        """Map Graph API SKU IDs to Partner Center products"""
        mapping = {}

        for graph_sku_id in graph_sku_ids:
            partner_product = await self.get_partner_center_sku(graph_sku_id)
            mapping[graph_sku_id] = partner_product

            if partner_product:
                logger.info(
                    "sku_mapped",
                    graph_sku_id=graph_sku_id,
                    partner_product_id=partner_product.product_id,
                    partner_sku_id=partner_product.sku_id,
                )
            else:
                logger.warning("sku_mapping_not_found", graph_sku_id=graph_sku_id)

        return mapping

    async def get_compatible_addons(
        self,
        graph_base_sku_id: str,
        service_type: Optional[str] = None,
        addon_category: Optional[str] = None,
    ) -> List[Dict]:
        """Get compatible add-ons for a Graph base SKU"""
        partner_product = await self.get_partner_center_sku(graph_base_sku_id)

        if not partner_product:
            logger.error("partner_center_sku_not_found", graph_sku_id=graph_base_sku_id)
            return []

        # Get compatible add-ons from Partner Center perspective
        compatible_addons = await self.addon_repo.get_compatible_addons(
            partner_product.sku_id, service_type, addon_category
        )

        # Convert to Graph API perspective
        graph_addons = []
        for addon in compatible_addons:
            graph_addon_info = await self.get_graph_sku_info(addon.addon_sku_id)
            if graph_addon_info:
                graph_addon_info.update(
                    {
                        "partner_product_id": addon.addon_product_id,
                        "partner_sku_id": addon.addon_sku_id,
                        "compatibility_rules": {
                            "min_quantity": addon.min_quantity,
                            "max_quantity": addon.max_quantity,
                            "quantity_multiplier": addon.quantity_multiplier,
                            "requires_domain_validation": addon.requires_domain_validation,
                            "requires_tenant_validation": addon.requires_tenant_validation,
                        },
                    }
                )
                graph_addons.append(graph_addon_info)
            else:
                # If no Graph mapping exists, still include Partner Center info
                graph_addons.append(
                    {
                        "sku_id": addon.addon_sku_id,
                        "name": f"Partner Center Add-on: {addon.addon_sku_id}",
                        "partner_product_id": addon.addon_product_id,
                        "partner_sku_id": addon.addon_sku_id,
                        "compatibility_rules": {
                            "min_quantity": addon.min_quantity,
                            "max_quantity": addon.max_quantity,
                            "quantity_multiplier": addon.quantity_multiplier,
                            "requires_domain_validation": addon.requires_domain_validation,
                            "requires_tenant_validation": addon.requires_tenant_validation,
                        },
                    }
                )

        return graph_addons

    async def validate_addon_compatibility(
        self, graph_base_sku_id: str, graph_addon_sku_id: str, quantity: int
    ) -> Tuple[bool, Optional[str]]:
        """Validate if add-on is compatible with base SKU"""
        # Get Partner Center equivalents
        base_product = await self.get_partner_center_sku(graph_base_sku_id)
        addon_product = await self.get_partner_center_sku(graph_addon_sku_id)

        if not base_product:
            return False, f"Base SKU '{graph_base_sku_id}' not found in Partner Center"

        if not addon_product:
            # Try direct SKU validation without Graph mapping
            is_valid = await self.addon_repo.validate_compatibility(
                graph_addon_sku_id, base_product.sku_id, quantity
            )

            if is_valid:
                return True, None
            else:
                return (
                    False,
                    f"Add-on SKU '{graph_addon_sku_id}' is not compatible with base SKU '{graph_base_sku_id}'",
                )

        # Validate using Partner Center mapping
        is_valid = await self.addon_repo.validate_compatibility(
            addon_product.sku_id, base_product.sku_id, quantity
        )

        if is_valid:
            return True, None
        else:
            return (
                False,
                f"Add-on '{graph_addon_sku_id}' is not compatible with base '{graph_base_sku_id}' at quantity {quantity}",
            )

    async def get_sku_mapping_summary(self) -> Dict:
        """Get summary of SKU mappings"""
        # Get all Partner Center products
        all_products = await self.product_repo.get_all(limit=1000)

        # Get all compatibility mappings
        all_mappings = await self.addon_repo.get_all(limit=1000)

        # Calculate statistics
        total_products = len(all_products)
        total_mappings = len(all_mappings)

        active_mappings = sum(1 for mapping in all_mappings if mapping.is_active)

        service_types = {}
        addon_categories = {}

        for mapping in all_mappings:
            service_types[mapping.service_type] = (
                service_types.get(mapping.service_type, 0) + 1
            )
            addon_categories[mapping.addon_category] = (
                addon_categories.get(mapping.addon_category, 0) + 1
            )

        return {
            "total_partner_center_products": total_products,
            "total_compatibility_mappings": total_mappings,
            "active_mappings": active_mappings,
            "service_type_distribution": service_types,
            "addon_category_distribution": addon_categories,
            "mapping_coverage": active_mappings / total_mappings
            if total_mappings > 0
            else 0,
        }

    async def create_mapping(
        self,
        addon_sku_id: str,
        addon_product_id: str,
        base_sku_id: str,
        base_product_id: str,
        service_type: str,
        addon_category: str,
        **kwargs,
    ) -> AddonCompatibility:
        """Create a new compatibility mapping"""
        mapping_data = {
            "addon_sku_id": addon_sku_id,
            "addon_product_id": addon_product_id,
            "base_sku_id": base_sku_id,
            "base_product_id": base_product_id,
            "service_type": service_type,
            "addon_category": addon_category,
            **kwargs,
        }

        return await self.addon_repo.create(**mapping_data)

    async def update_mapping(
        self, mapping_id: UUID, **kwargs
    ) -> Optional[AddonCompatibility]:
        """Update an existing compatibility mapping"""
        mapping = await self.addon_repo.get_by_id(mapping_id)

        if not mapping:
            return None

        return await self.addon_repo.update(mapping, **kwargs)

    async def delete_mapping(self, mapping_id: UUID) -> bool:
        """Delete a compatibility mapping"""
        mapping = await self.addon_repo.get_by_id(mapping_id)

        if not mapping:
            return False

        await self.addon_repo.delete(mapping)
        return True
