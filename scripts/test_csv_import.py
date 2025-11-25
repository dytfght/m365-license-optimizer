#!/usr/bin/env python3
"""
Test script for importing Microsoft pricing CSV
Usage: cd backend && python ../scripts/test_csv_import.py
"""
import asyncio
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sys
import os

# Change to backend directory for imports to work
backend_dir = Path(__file__).parent.parent / "backend"
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models import MicrosoftProduct, MicrosoftPrice


async def import_csv_direct(csv_path: Path):
    """Import CSV directly without using the service (to avoid import issues)"""
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    print(f"📂 CSV file found: {csv_path}")
    print(f"📊 File size: {csv_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    stats = {"products": 0, "prices": 0, "errors": []}
    
    async with async_session() as session:
        print("\n🚀 Starting CSV import...")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                products_map = {}
                prices_dict = {}  # Use dict to auto-deduplicate
                
                for line_num, row in enumerate(reader, start=2):
                    try:
                        # Validate required ENUM fields
                        if not row.get('BillingPlan') or row['BillingPlan'] not in ('Annual', 'Monthly'):
                            stats['errors'].append(f"Line {line_num}: Invalid BillingPlan '{row.get('BillingPlan')}'")
                            continue
                        
                        if not row.get('Segment') or row['Segment'] not in ('Commercial', 'Education', 'Charity'):
                            stats['errors'].append(f"Line {line_num}: Invalid Segment '{row.get('Segment')}'")
                            continue
                        
                        # Create product
                        product_key = (row['ProductId'], row['SkuId'])
                        if product_key not in products_map:
                            product = MicrosoftProduct(
                                product_id=row['ProductId'],
                                sku_id=row['SkuId'],
                                product_title=row['ProductTitle'],
                                sku_title=row['SkuTitle'],
                                publisher=row.get('Publisher', 'Microsoft Corporation'),
                                sku_description=row.get('SkuDescription'),
                                unit_of_measure=row.get('UnitOfMeasure'),
                                tags=[t.strip() for t in row.get('Tags', '').split(';') if t.strip()]
                            )
                            products_map[product_key] = product
                        
                        # Create price with unique key (same as DB constraint)
                        effective_start = datetime.fromisoformat(row['EffectiveStartDate'].replace('Z', '+00:00'))
                        price_key = (
                            row['ProductId'],
                            row['SkuId'],
                            row['Market'],
                            row['Currency'],
                            row['Segment'],
                            row['BillingPlan'],
                            effective_start
                        )
                        
                        # Skip if duplicate (keep first occurrence)
                        if price_key in prices_dict:
                            stats['errors'].append(f"Line {line_num}: Duplicate price variant (skipped)")
                            continue
                        
                        price = MicrosoftPrice(
                            product_id=row['ProductId'],
                            sku_id=row['SkuId'],
                            market=row['Market'],
                            currency=row['Currency'],
                            segment=row['Segment'],
                            term_duration=row['TermDuration'],
                            billing_plan=row['BillingPlan'],
                            unit_price=Decimal(row['UnitPrice']),
                            erp_price=Decimal(row['ERP Price']),
                            effective_start_date=effective_start,
                            effective_end_date=datetime.fromisoformat(row['EffectiveEndDate'].replace('Z', '+00:00')),
                            change_indicator=row.get('ChangeIndicator', 'Unchanged'),
                            pricing_tier_range_min=int(row['PricingTierRangeMin']) if row.get('PricingTierRangeMin') else None,
                            pricing_tier_range_max=int(row['PricingTierRangeMax']) if row.get('PricingTierRangeMax') else None,
                        )
                        prices_dict[price_key] = price
                        
                    except Exception as e:
                        stats['errors'].append(f"Line {line_num}: {str(e)}")
            
            # Bulk insert
            session.add_all(products_map.values())
            await session.flush()
            stats['products'] = len(products_map)
            
            session.add_all(prices_dict.values())
            await session.flush()
            stats['prices'] = len(prices_dict)
            
            await session.commit()
            
            print("\n✅ Import completed!")
            print(f"   📦 Products: {stats['products']}")
            print(f"   💰 Prices: {stats['prices']}")
            print(f"   ❌ Errors: {len(stats['errors'])}")
            
            if stats['errors']:
                print("\n⚠️  First 5 errors:")
                for error in stats['errors'][:5]:
                    print(f"   - {error}")
                    
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Import failed: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Microsoft Pricing CSV Import Test")
    print("=" * 60)
    
    csv_path = backend_dir.parent / "downloads" / "Nov_NCE_LicenseBasedPL_GA_AX.csv"
    asyncio.run(import_csv_direct(csv_path))

