#!/usr/bin/env python3
"""
Script de test pour diagnostiquer les erreurs API (422 et 500)
Tests spécifiques pour LOT 12 - Reports et Sync
"""
import asyncio
import sys
import os
from pathlib import Path

# Ajouter le backend au path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx
import json
from dotenv import load_dotenv

load_dotenv(backend_path / ".env")


class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def login(self, email, password):
        """Connecter un utilisateur et obtenir un token"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                data={"username": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"✅ Login réussi - Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login échoué - Status: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur lors du login: {e}")
            return False

    async def test_sync_endpoints(self, tenant_id):
        """Tester les endpoints de synchronisation"""
        print(f"\n🔄 Test sync endpoints pour tenant {tenant_id}")

        headers = {"Authorization": f"Bearer {self.token}"}

        # Test sync_licenses
        print("\n📋 Test: sync_licenses")
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/tenants/{tenant_id}/sync_licenses",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 422:
                print(f"   ❌ Validation Error: {response.json()}")
            elif response.status_code >= 400:
                print(f"   ❌ Error: {response.text}")
            else:
                print(f"   ✅ Success: {response.json()}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

        # Test sync_usage
        print("\n📊 Test: sync_usage")
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/tenants/{tenant_id}/sync_usage",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 422:
                print(f"   ❌ Validation Error: {response.json()}")
            elif response.status_code >= 400:
                print(f"   ❌ Error: {response.text}")
            else:
                print(f"   ✅ Success: {response.json()}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    async def test_report_generation(self, analysis_id):
        """Tester la génération de rapports"""
        print(f"\n📄 Test report generation pour analysis {analysis_id}")

        headers = {"Authorization": f"Bearer {self.token}", "Accept-Language": "fr"}

        # Test PDF
        print("\n📄 Test: generate_pdf")
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/reports/analyses/{analysis_id}/pdf",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 500:
                print(f"   ❌ Internal Error - Response: {response.text}")
                print(f"   📝 Headers: {response.headers}")
            elif response.status_code >= 400:
                print(f"   ❌ Error: {response.text}")
            else:
                print(f"   ✅ Success - Report ID: {response.json().get('id')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            import traceback
            traceback.print_exc()

        # Test Excel
        print("\n📊 Test: generate_excel")
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/reports/analyses/{analysis_id}/excel",
                headers=headers
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 500:
                print(f"   ❌ Internal Error - Response: {response.text}")
            elif response.status_code >= 400:
                print(f"   ❌ Error: {response.text}")
            else:
                print(f"   ✅ Success - Report ID: {response.json().get('id')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

    async def get_tenant_info(self, tenant_id):
        """Obtenir les informations d'un tenant"""
        print(f"\nℹ️  Get tenant info: {tenant_id}")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/tenants/{tenant_id}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Tenant trouvé: {data.get('name')}")
                return data
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None

    async def get_analysis_info(self, analysis_id):
        """Obtenir les informations d'une analyse"""
        print(f"\nℹ️  Get analysis info: {analysis_id}")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/analyses/analyses/{analysis_id}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Analyse trouvée: {data.get('id')}")
                return data
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None

    async def close(self):
        await self.client.aclose()


async def main():
    """Fonction principale de test"""
    print("🔍 Test API - Diagnostic des erreurs 422/500")
    print("=" * 60)

    # Configuration
    BASE_URL = "http://localhost:8000"
    EMAIL = os.getenv("TEST_USER_EMAIL", "admin@example.com")
    PASSWORD = os.getenv("TEST_USER_PASSWORD", "admin123")
    TENANT_ID = "2751a3f3-4c8d-43a2-818a-ec15883379ff"  # L'ID de votre message
    ANALYSIS_ID = "26f63590-725f-4ca1-b31b-871ad1675d54"  # L'ID de votre message

    tester = APITester(BASE_URL)

    try:
        # 1. Login
        if not await tester.login(EMAIL, PASSWORD):
            print("❌ Impossible de se connecter, arrêt du test")
            return

        # 2. Vérifier le tenant
        tenant = await tester.get_tenant_info(TENANT_ID)
        if not tenant:
            print("❌ Tenant non trouvé, tests de sync annulés")
        else:
            # 3. Tester sync endpoints
            await tester.test_sync_endpoints(TENANT_ID)

        # 4. Vérifier l'analyse
        analysis = await tester.get_analysis_info(ANALYSIS_ID)
        if not analysis:
            print("❌ Analyse non trouvée, tests de rapport annulés")
            print("   💡 Vous devez d'abord créer et exécuter une analyse")
        else:
            # 5. Tester report generation
            await tester.test_report_generation(ANALYSIS_ID)

        print("\n" + "=" * 60)
        print("✅ Tests terminés. Vérifiez les erreurs ci-dessus.")

    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
