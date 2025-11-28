#!/usr/bin/env python3
"""
Test des API de rapport via HTTP
"""
import asyncio
import aiohttp
import json
import sys
from uuid import uuid4
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MGE4NDUwNy1iMTc3LTRhOWYtYWU4Yi1hZmU1MGYyZWE4ZDAiLCJlbWFpbCI6InRlc3QtYXBpQGV4YW1wbGUuY29tIiwiZXhwIjoxNzY0Mzc0NDI2LCJpYXQiOjE3NjQzNzA4MjYsInR5cGUiOiJhY2Nlc3MifQ.xhUmwopv9k6u3j4jdu_A4VdgqNLBes3ZLymmAJPwmyM"

async def test_api_reports():
    """Test les API de rapport"""
    
    headers = {
        "Authorization": f"Bearer {TEST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("1️⃣ Test de la version de l'API...")
            async with session.get(f"{BASE_URL}/api/v1/version") as resp:
                version_data = await resp.json()
                print(f"   ✅ Version: {version_data}")
            
            print("\n2️⃣ Test de la liste des reports...")
            async with session.get(f"{BASE_URL}/api/v1/reports/analyses/3cd323d6-d5ad-41dd-97d2-3de500d11361", headers=headers) as resp:
                list_data = await resp.json()
                print(f"   📊 Reports trouvés: {list_data.get('total', 0)}")
            
            print("\n3️⃣ Test de génération de rapport PDF...")
            analysis_id = "3cd323d6-d5ad-41dd-97d2-3de500d11361"
            
            async with session.post(f"{BASE_URL}/api/v1/reports/analyses/{analysis_id}/pdf", headers=headers) as resp:
                if resp.status == 201:
                    pdf_data = await resp.json()
                    print(f"   ✅ Rapport PDF créé: {pdf_data.get('id')}")
                    print(f"   📄 Fichier: {pdf_data.get('file_name')}")
                    print(f"   📏 Taille: {pdf_data.get('file_size')} bytes")
                    
                    # Test de téléchargement
                    report_id = pdf_data.get('id')
                    print(f"\n4️⃣ Test de téléchargement du rapport {report_id}...")
                    
                    async with session.get(f"{BASE_URL}/api/v1/reports/{report_id}/download", headers=headers) as download_resp:
                        if download_resp.status == 200:
                            download_data = await download_resp.json()
                            print(f"   ✅ Téléchargement disponible: {download_data.get('download_url')}")
                        else:
                            print(f"   ❌ Erreur téléchargement: {download_resp.status}")
                    
                    # Test Excel
                    print(f"\n5️⃣ Test de génération de rapport Excel...")
                    async with session.post(f"{BASE_URL}/api/v1/reports/analyses/{analysis_id}/excel", headers=headers) as excel_resp:
                        if excel_resp.status == 201:
                            excel_data = await excel_resp.json()
                            print(f"   ✅ Rapport Excel créé: {excel_data.get('id')}")
                            print(f"   📄 Fichier: {excel_data.get('file_name')}")
                            print(f"   📏 Taille: {excel_data.get('file_size')} bytes")
                        else:
                            print(f"   ❌ Erreur Excel: {excel_resp.status}")
                            error_text = await excel_resp.text()
                            print(f"   📋 Erreur: {error_text}")
                    
                    return True
                    
                elif resp.status == 404:
                    print(f"   ❌ Analysis non trouvée: {analysis_id}")
                else:
                    error_text = await resp.text()
                    print(f"   ❌ Erreur {resp.status}: {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🧪 Test des API de rapport")
    success = asyncio.run(test_api_reports())
    if success:
        print("\n🎉 Tests API réussis!")
    else:
        print("\n💥 Tests API échoués!")
        sys.exit(1)