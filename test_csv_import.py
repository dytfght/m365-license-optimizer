#!/usr/bin/env python3
"""
Test script for importing Microsoft pricing CSV
"""
import asyncio
import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.src.services.price_import_service import PriceImportService
from backend.src.core.config import settings


async def test_csv_import():
    """Test importing the CSV file"""
    
    # CSV file path
    csv_path = Path(__file__).parent / "downloads" / "Nov_NCE_LicenseBasedPL_GA_AX.csv"
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    print(f"📂 CSV file found: {csv_path}")
    print(f"📊 File size: {csv_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Import CSV
    async with async_session() as session:
        print("\n🚀 Starting CSV import...")
        service = PriceImportService(session)
        
        try:
            stats = await service.import_csv(csv_path)
            
            print("\n✅ Import completed!")
            print(f"   📦 Products processed: {stats['products']}")
            print(f"   💰 Prices processed: {stats['prices']}")
            print(f"   ❌ Errors: {len(stats['errors'])}")
            
            if stats['errors']:
                print("\n⚠️  First 5 errors:")
                for error in stats['errors'][:5]:
                    print(f"   - {error}")
                    
        except Exception as e:
            print(f"\n❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Microsoft Pricing CSV Import Test")
    print("=" * 60)
    asyncio.run(test_csv_import())
