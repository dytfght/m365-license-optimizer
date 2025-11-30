#!/usr/bin/env python3
"""
LOT8 Setup Script
Setup script for deploying LOT8: SKU mapping and add-on compatibility
"""
import asyncio
import logging
import os
import sys
import subprocess
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


def run_alembic_migration():
    """Run Alembic migration for LOT8"""
    logger.info("Running Alembic migration for LOT8...")
    
    try:
        # Change to backend directory
        os.chdir(backend_dir)
        
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info("Alembic migration completed successfully")
        logger.info(f"Migration output: {result.stdout}")
        
        if result.stderr:
            logger.warning(f"Migration warnings: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Alembic migration failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        raise


async def run_sku_mapping_seeder():
    """Run SKU mapping seeder"""
    logger.info("Running SKU mapping seeder...")
    
    try:
        # Import the seeder
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        from src.core.config import settings
        from scripts.seed_sku_mappings import SkuMappingSeeder
        
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
            
        logger.info("SKU mapping seeder completed successfully")
        
    except Exception as e:
        logger.error(f"SKU mapping seeder failed: {e}")
        raise


def verify_lot8_installation():
    """Verify LOT8 installation"""
    logger.info("Verifying LOT8 installation...")
    
    try:
        # Import required modules to check if they can be loaded
        from src.models.addon_compatibility import AddonCompatibility
        from src.services.sku_mapping_service import SkuMappingService
        from src.services.partner_center_addons_service import PartnerCenterAddonsService
        from src.services.addon_validator import AddonValidator
        from src.api.v1.endpoints.admin_sku_mapping import router
        
        logger.info("✓ All LOT8 modules loaded successfully")
        
        # Check if the router has the expected endpoints
        routes = [route.path for route in router.routes]
        expected_routes = [
            "/summary",
            "/sync/products",
            "/sync/compatibility",
            "/compatible-addons",
            "/validate-addon",
            "/compatibility-mappings",
            "/recommendations"
        ]
        
        for expected_route in expected_routes:
            matching_routes = [route for route in routes if expected_route in route]
            if matching_routes:
                logger.info(f"✓ Found route: {expected_route}")
            else:
                logger.warning(f"⚠ Route not found: {expected_route}")
        
        logger.info("LOT8 verification completed")
        
    except ImportError as e:
        logger.error(f"Failed to import LOT8 modules: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise


def main():
    """Main setup function"""
    logger.info("Starting LOT8 setup...")
    
    try:
        # Step 1: Run database migration
        logger.info("Step 1: Running database migration...")
        run_alembic_migration()
        
        # Step 2: Run SKU mapping seeder
        logger.info("Step 2: Running SKU mapping seeder...")
        asyncio.run(run_sku_mapping_seeder())
        
        # Step 3: Verify installation
        logger.info("Step 3: Verifying installation...")
        verify_lot8_installation()
        
        logger.info("🎉 LOT8 setup completed successfully!")
        logger.info("SKU mapping and add-on compatibility features are now available.")
        
    except Exception as e:
        logger.error(f"❌ LOT8 setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()