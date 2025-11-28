#!/usr/bin/env python3
"""
Test rapide de génération de rapports pour le Lot 7
"""
import asyncio
import sys
import os

# Ajouter le backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from uuid import UUID
from sqlalchemy import select
from src.core.database import AsyncSessionLocal
from src.models.analysis import Analysis
from src.models.report import Report
from src.services.reports.report_service import ReportService
from src.services.reports.pdf_generator import PDFGenerator
from src.services.reports.excel_generator_simple import ExcelGenerator


async def test_report_generation():
    """Test rapide de génération de rapports"""
    
    print("🧪 Test de génération de rapports - Lot 7")
    
    async with AsyncSessionLocal() as session:
        try:
            # Récupérer une analyse existante
            result = await session.execute(
                select(Analysis).limit(1)
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                print("❌ Aucune analyse trouvée. Créez d'abord une analyse.")
                return
            
            print(f"✅ Analyse trouvée: {analysis.id}")
            
            # Test 1: Génération PDF
            print("\n📄 Test génération PDF...")
            
            report_service = ReportService(session)
            
            # Données de test
            test_data = {
                "analysis_id": str(analysis.id),
                "tenant_id": str(analysis.tenant_client_id),
                "title": "Analyse d'optimisation Microsoft 365 - Test",
                "period_start": "01/11/2024",
                "period_end": "28/11/2024",
                "kpis": {
                    "current_monthly_cost": 15420.0,
                    "target_monthly_cost": 11570.0,
                    "monthly_savings": 3850.0,
                    "annual_savings": 46200.0,
                    "savings_percentage": 25.0,
                    "total_users": 247
                },
                "license_distribution": [
                    {"license_name": "Microsoft 365 E5", "user_count": 50, "percentage": 25.0},
                    {"license_name": "Microsoft 365 E3", "user_count": 80, "percentage": 40.0},
                    {"license_name": "Microsoft 365 Business Premium", "user_count": 40, "percentage": 20.0},
                    {"license_name": "Microsoft 365 Business Standard", "user_count": 20, "percentage": 10.0},
                    {"license_name": "Microsoft 365 Business Basic", "user_count": 10, "percentage": 5.0},
                ],
                "top_recommendations": [
                    {
                        "count": 25,
                        "from_license": "Microsoft 365 E5",
                        "to_license": "Microsoft 365 E3",
                        "monthly_savings": 1250.0,
                        "annual_savings": 15000.0
                    },
                    {
                        "count": 15,
                        "from_license": "Comptes inactifs",
                        "to_license": "Désaffectation",
                        "monthly_savings": 750.0,
                        "annual_savings": 9000.0
                    },
                    {
                        "count": 10,
                        "from_license": "Microsoft 365 Business Premium",
                        "to_license": "Microsoft 365 Business Standard",
                        "monthly_savings": 500.0,
                        "annual_savings": 6000.0
                    }
                ],
                "departments": [
                    {
                        "name": "IT",
                        "user_count": 45,
                        "current_cost": 3200.0,
                        "target_cost": 2400.0,
                        "annual_savings": 9600.0
                    },
                    {
                        "name": "Sales",
                        "user_count": 60,
                        "current_cost": 4200.0,
                        "target_cost": 3150.0,
                        "annual_savings": 12600.0
                    }
                ],
                "metadata": {
                    "generated_at": "2024-11-28T15:30:00Z",
                    "report_version": "1.0",
                    "tenant_name": "Test Tenant"
                }
            }
            
            # Test PDF generator directly
            pdf_generator = PDFGenerator()
            pdf_content = await pdf_generator.generate_executive_summary(test_data)
            
            print(f"✅ PDF généré: {len(pdf_content)} bytes")
            
            # Test Excel generator directly
            print("\n📊 Test génération Excel...")
            
            excel_generator = ExcelGenerator()
            excel_content = await excel_generator.generate_detailed_excel(test_data)
            
            print(f"✅ Excel généré: {len(excel_content)} bytes")
            
            # Test via service
            print("\n🔄 Test via ReportService...")
            
            # Générer un rapport PDF via le service
            pdf_report = await report_service.generate_pdf_report(
                analysis_id=analysis.id,
                generated_by="test@example.com"
            )
            
            print(f"✅ Rapport PDF créé en base: {pdf_report.id}")
            print(f"   Fichier: {pdf_report.file_name}")
            print(f"   Type: {pdf_report.report_type}")
            print(f"   Taille: {pdf_report.file_size_bytes} bytes")
            
            # Générer un rapport Excel via le service
            excel_report = await report_service.generate_excel_report(
                analysis_id=analysis.id,
                generated_by="test@example.com"
            )
            
            print(f"✅ Rapport Excel créé en base: {excel_report.id}")
            print(f"   Fichier: {excel_report.file_name}")
            print(f"   Type: {excel_report.report_type}")
            print(f"   Taille: {excel_report.file_size_bytes} bytes")
            
            # Vérifier que les rapports sont bien enregistrés
            reports = await report_service.get_reports_by_analysis(analysis.id)
            print(f"\n📋 Rapports trouvés pour cette analyse: {len(reports)}")
            
            for report in reports:
                print(f"   - {report.report_type}: {report.file_name} ({report.file_size_bytes} bytes)")
            
            print("\n🎉 Tests terminés avec succès!")
            print("✅ Le Lot 7 (Rapports PDF/Excel) est fonctionnel!")
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_report_generation())