#!/usr/bin/env python3
"""
SKU Mapping Seeder
Seed script for populating SKU mappings and add-on compatibility data
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.models.addon_compatibility import AddonCompatibility
from src.models.microsoft_product import MicrosoftProduct
from src.repositories.addon_compatibility_repository import AddonCompatibilityRepository
from src.repositories.product_repository import ProductRepository
from src.services.partner_center_addons_service import PartnerCenterAddonsService
from src.services.sku_mapping_service import SkuMappingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkuMappingSeeder:
    """Seeder for SKU mappings and add-on compatibility"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repo = ProductRepository(session)
        self.addon_repo = AddonCompatibilityRepository(session)
        self.sku_service = SkuMappingService(session)
        self.pc_service = PartnerCenterAddonsService(session)

    async def seed_microsoft_products(self) -> None:
        """Seed Microsoft products from Partner Center"""
        logger.info("Seeding Microsoft products...")
        
        # Mock Microsoft 365 products
        products_data = [
            # Base SKUs
            {
                "product_id": "CFQ7TTC0LF8S",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Business",
                "sku_title": "Microsoft 365 Business Premium",
                "sku_description": "Complete productivity and collaboration solution for small businesses",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0LH0B",
                "sku_id": "0001", 
                "product_title": "Microsoft 365 E3",
                "sku_title": "Microsoft 365 E3",
                "sku_description": "Enterprise productivity suite with advanced security",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0LH0C",
                "sku_id": "0001",
                "product_title": "Microsoft 365 E5",
                "sku_title": "Microsoft 365 E5", 
                "sku_description": "Most comprehensive Microsoft 365 plan with advanced analytics",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0LH0D",
                "sku_id": "0001",
                "product_title": "Office 365 E1",
                "sku_title": "Office 365 E1",
                "sku_description": "Online versions of Office with Teams",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0LH0E",
                "sku_id": "0001",
                "product_title": "Office 365 E3",
                "sku_title": "Office 365 E3",
                "sku_description": "Full Office suite with advanced compliance",
                "publisher": "Microsoft Corporation"
            },
            # Add-on SKUs
            {
                "product_id": "CFQ7TTC0P0HP",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Audio Conferencing",
                "sku_title": "Microsoft 365 Audio Conferencing",
                "sku_description": "Enable PSTN conferencing for Microsoft Teams",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HQ",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Phone System",
                "sku_title": "Microsoft 365 Phone System",
                "sku_description": "Cloud-based phone system for Microsoft Teams",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HR",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Domestic Calling Plan",
                "sku_title": "Microsoft 365 Domestic Calling Plan",
                "sku_description": "Domestic calling minutes for Microsoft Teams",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HS",
                "sku_id": "0001",
                "product_title": "Microsoft 365 International Calling Plan",
                "sku_title": "Microsoft 365 International Calling Plan",
                "sku_description": "International calling minutes for Microsoft Teams",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HT",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Audio Conferencing Pay Per Minute",
                "sku_title": "Microsoft 365 Audio Conferencing Pay Per Minute",
                "sku_description": "Pay-per-minute audio conferencing for Microsoft Teams",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HU",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Advanced Compliance",
                "sku_title": "Microsoft 365 Advanced Compliance",
                "sku_description": "Advanced compliance features for Microsoft 365",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HV",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Advanced Threat Protection",
                "sku_title": "Microsoft 365 Advanced Threat Protection",
                "sku_description": "Advanced threat protection for Microsoft 365",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HW",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Power BI Pro",
                "sku_title": "Microsoft 365 Power BI Pro",
                "sku_description": "Business intelligence and analytics with Power BI Pro",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HX",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Project Plan 3",
                "sku_title": "Microsoft 365 Project Plan 3",
                "sku_description": "Project management capabilities with Project Plan 3",
                "publisher": "Microsoft Corporation"
            },
            {
                "product_id": "CFQ7TTC0P0HY",
                "sku_id": "0001",
                "product_title": "Microsoft 365 Visio Plan 2",
                "sku_title": "Microsoft 365 Visio Plan 2",
                "sku_description": "Diagramming and vector graphics with Visio Plan 2",
                "publisher": "Microsoft Corporation"
            }
        ]
        
        created_count = 0
        for product_data in products_data:
            # Check if product already exists
            existing = await self.product_repo.get_by_product_and_sku(
                product_data["product_id"],
                product_data["sku_id"]
            )
            
            if not existing:
                await self.product_repo.create(**product_data)
                created_count += 1
                logger.info(f"Created product: {product_data['product_title']}")
            else:
                logger.info(f"Product already exists: {product_data['product_title']}")
        
        logger.info(f"Seeded {created_count} new Microsoft products")

    async def seed_addon_compatibility(self) -> None:
        """Seed add-on compatibility mappings"""
        logger.info("Seeding add-on compatibility mappings...")
        
        # Define compatibility mappings
        compatibility_mappings = [
            # Audio Conferencing compatibility
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HP",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LF8S",
                "service_type": "Microsoft 365",
                "addon_category": "Audio Conferencing",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Audio Conferencing for Microsoft 365 Business Premium",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HP",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0B",
                "service_type": "Microsoft 365",
                "addon_category": "Audio Conferencing",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Audio Conferencing for Microsoft 365 E3",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HP",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0C",
                "service_type": "Microsoft 365",
                "addon_category": "Audio Conferencing",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Audio Conferencing for Microsoft 365 E5",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HP",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0E",
                "service_type": "Microsoft 365",
                "addon_category": "Audio Conferencing",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Audio Conferencing for Office 365 E3",
                "is_active": True
            },
            # Phone System compatibility
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HQ",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0B",
                "service_type": "Microsoft 365",
                "addon_category": "Phone System",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": True,
                "requires_tenant_validation": True,
                "description": "Phone System for Microsoft 365 E3",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HQ",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0C",
                "service_type": "Microsoft 365",
                "addon_category": "Phone System",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": True,
                "requires_tenant_validation": True,
                "description": "Phone System for Microsoft 365 E5",
                "is_active": True
            },
            # Calling Plan compatibility (requires Phone System)
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HR",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0P0HQ",
                "service_type": "Microsoft 365",
                "addon_category": "Calling Plan",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Domestic Calling Plan for Phone System",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HS",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0P0HQ",
                "service_type": "Microsoft 365",
                "addon_category": "Calling Plan",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "International Calling Plan for Phone System",
                "is_active": True
            },
            # Advanced Compliance compatibility
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HU",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0B",
                "service_type": "Microsoft 365",
                "addon_category": "Advanced Compliance",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Advanced Compliance for Microsoft 365 E3",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HU",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0C",
                "service_type": "Microsoft 365",
                "addon_category": "Advanced Compliance",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Advanced Compliance for Microsoft 365 E5",
                "is_active": True
            },
            # Advanced Threat Protection compatibility
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HV",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0B",
                "service_type": "Microsoft 365",
                "addon_category": "Advanced Threat Protection",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Advanced Threat Protection for Microsoft 365 E3",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HV",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0C",
                "service_type": "Microsoft 365",
                "addon_category": "Advanced Threat Protection",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Advanced Threat Protection for Microsoft 365 E5",
                "is_active": True
            },
            # Power BI Pro compatibility
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HW",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0B",
                "service_type": "Microsoft 365",
                "addon_category": "Analytics",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Power BI Pro for Microsoft 365 E3",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HW",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0C",
                "service_type": "Microsoft 365",
                "addon_category": "Analytics",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Power BI Pro for Microsoft 365 E5",
                "is_active": True
            },
            # Project Plan 3 compatibility
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HX",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0B",
                "service_type": "Microsoft 365",
                "addon_category": "Project Management",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Project Plan 3 for Microsoft 365 E3",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HX",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0C",
                "service_type": "Microsoft 365",
                "addon_category": "Project Management",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Project Plan 3 for Microsoft 365 E5",
                "is_active": True
            },
            # Visio Plan 2 compatibility
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HY",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0B",
                "service_type": "Microsoft 365",
                "addon_category": "Diagramming",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Visio Plan 2 for Microsoft 365 E3",
                "is_active": True
            },
            {
                "addon_sku_id": "0001",
                "addon_product_id": "CFQ7TTC0P0HY",
                "base_sku_id": "0001",
                "base_product_id": "CFQ7TTC0LH0C",
                "service_type": "Microsoft 365",
                "addon_category": "Diagramming",
                "min_quantity": 1,
                "max_quantity": None,
                "quantity_multiplier": 1,
                "requires_domain_validation": False,
                "requires_tenant_validation": False,
                "description": "Visio Plan 2 for Microsoft 365 E5",
                "is_active": True
            }
        ]
        
        created_count = 0
        for mapping_data in compatibility_mappings:
            # Check if mapping already exists
            existing = await self.addon_repo.get_specific_mapping(
                mapping_data["addon_sku_id"],
                mapping_data["base_sku_id"]
            )
            
            if not existing:
                await self.addon_repo.create(**mapping_data)
                created_count += 1
                logger.info(
                    f"Created compatibility mapping: {mapping_data['addon_category']} "
                    f"for {mapping_data['base_product_id']} -> {mapping_data['addon_product_id']}"
                )
            else:
                logger.info(f"Compatibility mapping already exists: {mapping_data['addon_category']}")
        
        logger.info(f"Seeded {created_count} new compatibility mappings")

    async def seed_graph_to_partner_center_mapping(self) -> None:
        """Seed Graph API to Partner Center SKU mappings"""
        logger.info("Seeding Graph API to Partner Center mappings...")
        
        # This would typically be stored in a separate mapping table
        # For now, we'll just log the mappings that would be created
        graph_mappings = {
            "O365_BUSINESS_PREMIUM": "CFQ7TTC0LF8S:0001",
            "ENTERPRISEPACK": "CFQ7TTC0LH0E:0001",  # Office 365 E3
            "SPE_E3": "CFQ7TTC0LH0B:0001",         # Microsoft 365 E3
            "SPE_E5": "CFQ7TTC0LH0C:0001",         # Microsoft 365 E5
            "STANDARDPACK": "CFQ7TTC0LH0D:0001",   # Office 365 E1
        }
        
        for graph_sku, partner_sku in graph_mappings.items():
            logger.info(f"Graph SKU {graph_sku} -> Partner Center {partner_sku}")
        
        logger.info(f"Defined {len(graph_mappings)} Graph to Partner Center mappings")

    async def run_seeding(self) -> None:
        """Run the complete seeding process"""
        try:
            logger.info("Starting SKU mapping seeding process...")
            
            # Seed Microsoft products
            await self.seed_microsoft_products()
            
            # Seed add-on compatibility mappings
            await self.seed_addon_compatibility()
            
            # Seed Graph API mappings
            await self.seed_graph_to_partner_center_mapping()
            
            # Commit all changes
            await self.session.commit()
            
            logger.info("SKU mapping seeding completed successfully!")
            
            # Show summary
            summary = await self.sku_service.get_sku_mapping_summary()
            logger.info(f"Seeding summary: {summary}")
            
        except Exception as e:
            logger.error(f"Seeding failed: {str(e)}")
            await self.session.rollback()
            raise


async def main():
    """Main function to run the seeder"""
    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )
    
    # Create session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        seeder = SkuMappingSeeder(session)
        await seeder.run_seeding()


if __name__ == "__main__":
    asyncio.run(main())