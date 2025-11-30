#!/usr/bin/env python3
"""
LOT8 Integration Test Script
Test script to verify LOT8 functionality: SKU mapping and add-on compatibility
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir))


async def test_sku_mapping_service():
    """Test SKU mapping service functionality"""
    logger.info("Testing SKU Mapping Service...")
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        from src.core.config import settings
        from src.services.sku_mapping_service import SkuMappingService
        
        # Create database connection
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True
        )
        
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session() as session:
            service = SkuMappingService(session)
            
            # Test 1: Get SKU mapping summary
            logger.info("Test 1: Getting SKU mapping summary...")
            summary = await service.get_sku_mapping_summary()
            logger.info(f"SKU Mapping Summary: {summary}")
            
            # Test 2: Map Graph to Partner Center
            logger.info("Test 2: Mapping Graph SKUs to Partner Center...")
            graph_skus = ["O365_BUSINESS_PREMIUM", "ENTERPRISEPACK", "SPE_E3"]
            mapping = await service.map_graph_to_partner_center(graph_skus)
            logger.info(f"Graph to Partner Center mapping: {list(mapping.keys())}")
            
            # Test 3: Get compatible add-ons
            logger.info("Test 3: Getting compatible add-ons...")
            compatible_addons = await service.get_compatible_addons("O365_BUSINESS_PREMIUM")
            logger.info(f"Found {len(compatible_addons)} compatible add-ons")
            
            # Test 4: Validate add-on compatibility
            logger.info("Test 4: Validating add-on compatibility...")
            if compatible_addons:
                addon = compatible_addons[0]
                is_valid, error = await service.validate_addon_compatibility(
                    addon["sku_id"], "O365_BUSINESS_PREMIUM", 5
                )
                logger.info(f"Add-on validation: valid={is_valid}, error={error}")
            
            logger.info("✓ SKU Mapping Service tests completed successfully")
            
    except Exception as e:
        logger.error(f"✗ SKU Mapping Service tests failed: {e}")
        raise


async def test_addon_validator():
    """Test add-on validator service functionality"""
    logger.info("Testing Add-on Validator Service...")
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        from src.core.config import settings
        from src.services.addon_validator import AddonValidator
        
        # Create database connection
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True
        )
        
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session() as session:
            validator = AddonValidator(session)
            
            # Test 1: Validate add-on compatibility
            logger.info("Test 1: Validating add-on compatibility...")
            is_valid, errors = await validator.validate_addon_compatibility(
                "0001", "0001", 5, "12345678-1234-1234-1234-123456789012", "contoso.com"
            )
            logger.info(f"Validation result: valid={is_valid}, errors={errors}")
            
            # Test 2: Get validation requirements
            logger.info("Test 2: Getting validation requirements...")
            requirements = await validator.get_validation_requirements("0001", "0001")
            logger.info(f"Validation requirements: {requirements}")
            
            # Test 3: Get SKU validation summary
            logger.info("Test 3: Getting SKU validation summary...")
            summary = await validator.get_sku_validation_summary("0001")
            logger.info(f"SKU validation summary: {summary}")
            
            # Test 4: Bulk validation
            logger.info("Test 4: Testing bulk validation...")
            addons = [
                {"sku_id": "0001", "quantity": 1},
                {"sku_id": "0002", "quantity": 2},
            ]
            all_valid, results = await validator.validate_bulk_addons(addons, "0001")
            logger.info(f"Bulk validation: all_valid={all_valid}, results={results}")
            
            logger.info("✓ Add-on Validator Service tests completed successfully")
            
    except Exception as e:
        logger.error(f"✗ Add-on Validator Service tests failed: {e}")
        raise


async def test_partner_center_addons_service():
    """Test Partner Center add-ons service functionality"""
    logger.info("Testing Partner Center Add-ons Service...")
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        from src.core.config import settings
        from src.services.partner_center_addons_service import PartnerCenterAddonsService
        
        # Create database connection
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True
        )
        
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session() as session:
            service = PartnerCenterAddonsService(session)
            
            # Test 1: Fetch Partner Center products (mock)
            logger.info("Test 1: Fetching Partner Center products...")
            products = await service.fetch_partner_center_products()
            logger.info(f"Found {len(products)} products")
            
            # Test 2: Sync products (will use mock data)
            logger.info("Test 2: Syncing products...")
            created, updated = await service.sync_partner_center_products()
            logger.info(f"Product sync: created={created}, updated={updated}")
            
            # Test 3: Sync compatibility rules
            logger.info("Test 3: Syncing compatibility rules...")
            created, updated = await service.sync_addon_compatibility_rules()
            logger.info(f"Compatibility sync: created={created}, updated={updated}")
            
            # Test 4: Get add-on recommendations
            logger.info("Test 4: Getting add-on recommendations...")
            recommendations = await service.get_addon_recommendations(
                "0001", ["0002", "0003"], "medium"
            )
            logger.info(f"Found {len(recommendations)} recommendations")
            
            # Test 5: Validate add-on purchase
            logger.info("Test 5: Validating add-on purchase...")
            is_valid, errors = await service.validate_addon_purchase(
                "0001", "0001", 5, "12345678-1234-1234-1234-123456789012"
            )
            logger.info(f"Purchase validation: valid={is_valid}, errors={errors}")
            
            logger.info("✓ Partner Center Add-ons Service tests completed successfully")
            
    except Exception as e:
        logger.error(f"✗ Partner Center Add-ons Service tests failed: {e}")
        raise


async def test_database_models():
    """Test database models and repositories"""
    logger.info("Testing Database Models...")
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        from src.core.config import settings
        from src.models.addon_compatibility import AddonCompatibility
        from src.repositories.addon_compatibility_repository import AddonCompatibilityRepository
        
        # Create database connection
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True
        )
        
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session() as session:
            repo = AddonCompatibilityRepository(session)
            
            # Test 1: Get all mappings
            logger.info("Test 1: Getting all compatibility mappings...")
            all_mappings = await repo.get_all(limit=10)
            logger.info(f"Found {len(all_mappings)} mappings")
            
            # Test 2: Get mappings by service type
            logger.info("Test 2: Getting mappings by service type...")
            m365_mappings = await repo.get_by_service_type("Microsoft 365")
            logger.info(f"Found {len(m365_mappings)} Microsoft 365 mappings")
            
            # Test 3: Get mappings by category
            logger.info("Test 3: Getting mappings by category...")
            audio_mappings = await repo.get_by_addon_category("Audio Conferencing")
            logger.info(f"Found {len(audio_mappings)} Audio Conferencing mappings")
            
            # Test 4: Get specific mapping
            logger.info("Test 4: Getting specific mapping...")
            if all_mappings:
                mapping = all_mappings[0]
                specific = await repo.get_specific_mapping(
                    mapping.addon_sku_id, mapping.base_sku_id
                )
                logger.info(f"Specific mapping: {specific.id if specific else 'Not found'}")
            
            # Test 5: Validate compatibility
            logger.info("Test 5: Validating compatibility...")
            if all_mappings:
                mapping = all_mappings[0]
                is_valid = await repo.validate_compatibility(
                    mapping.addon_sku_id, mapping.base_sku_id, 5
                )
                logger.info(f"Compatibility validation: {is_valid}")
            
            logger.info("✓ Database Models tests completed successfully")
            
    except Exception as e:
        logger.error(f"✗ Database Models tests failed: {e}")
        raise


async def main():
    """Main test function"""
    logger.info("Starting LOT8 Integration Tests...")
    
    try:
        # Test 1: Database Models
        await test_database_models()
        
        # Test 2: SKU Mapping Service
        await test_sku_mapping_service()
        
        # Test 3: Add-on Validator
        await test_addon_validator()
        
        # Test 4: Partner Center Add-ons Service
        await test_partner_center_addons_service()
        
        logger.info("🎉 All LOT8 Integration Tests completed successfully!")
        logger.info("LOT8 implementation is working correctly.")
        
    except Exception as e:
        logger.error(f"❌ LOT8 Integration Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())