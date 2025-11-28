#!/usr/bin/env python3
"""
Test direct des services de rapport
"""
import asyncio
import sys
sys.path.append('/mnt/d/Doc G/Projets/m365-license-optimizer/backend')

from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.core.config import settings
from src.models.analysis import Analysis
from src.models.user import User
from src.models.tenant import TenantClient
from src.models.report import Report
from src.services.reports.report_service import ReportService
from src.repositories.analysis_repository import AnalysisRepository
from src.repositories.recommendation_repository import RecommendationRepository

async def test_report_generation():
    """Test direct de la génération de rapports"""
    
    # Créer une session de base de données
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Récupérer une analysis existante
            result = await session.execute(
                select(Analysis).limit(1)
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                print("⚠️ Aucune analysis trouvée, création d'une analysis de test...")
                
                # Créer un tenant
                tenant = TenantClient(
                    id=uuid4(),
                    name="Test Tenant",
                    tenant_id=str(uuid4()),
                    country="FR",
                    onboarding_status="active"
                )
                session.add(tenant)
                await session.flush()
                
                # Créer une analysis
                analysis = Analysis(
                    id=uuid4(),
                    tenant_client_id=tenant.id,
                    status="COMPLETED",
                    analysis_date=datetime.now(),
                    summary={
                        "total_users": 150,
                        "potential_savings": 12500.0,
                        "inactive_users": 25,
                        "underutilized_licenses": 45,
                        "total_current_cost": 50000.0,
                        "total_optimized_cost": 37500.0,
                        "potential_savings_monthly": 12500.0,
                        "potential_savings_annual": 150000.0
                    }
                )
                session.add(analysis)
                await session.commit()
            
            print(f"📝 Utilisation de l'analysis: {analysis.id}")
            print(f"📊 Résumé: {analysis.summary}")
            
            # Créer le service de rapport
            report_service = ReportService(session)
            
            print("🚀 Génération du rapport PDF...")
            
            # Générer le rapport PDF
            report = await report_service.generate_pdf_report(
                analysis_id=analysis.id,
                generated_by="test@example.com"
            )
            
            print(f"✅ Rapport PDF généré avec succès!")
            print(f"📄 ID du rapport: {report.id}")
            print(f"📁 Fichier: {report.file_name}")
            print(f"📏 Taille: {report.file_size_bytes} bytes")
            print(f"📋 Type: {report.report_type}")
            print(f"💾 Chemin: {report.file_path}")
            
            # Vérifier que le fichier existe
            import os
            if os.path.exists(report.file_path):
                print(f"✅ Le fichier existe sur le disque")
            else:
                print(f"❌ Le fichier n'existe pas sur le disque")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération du rapport: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await session.close()

if __name__ == "__main__":
    print("🧪 Test de génération de rapport PDF")
    success = asyncio.run(test_report_generation())
    if success:
        print("\n🎉 Test réussi!")
    else:
        print("\n💥 Test échoué!")
        sys.exit(1)