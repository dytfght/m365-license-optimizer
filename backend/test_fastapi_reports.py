#!/usr/bin/env python3
"""
Test des API de rapport via FastAPI TestClient
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime

from src.main import app
from src.core.database import get_db
from src.models.analysis import Analysis
from src.models.user import User
from src.models.tenant import TenantClient
from src.core.security import create_access_token, get_password_hash


@pytest_asyncio.fixture
async def test_user_and_analysis(db_session: AsyncSession):
    """Créer un utilisateur et une analysis de test"""
    # Créer un tenant
    tenant = TenantClient(
        id=uuid4(),
        name="Test Tenant API",
        tenant_id=str(uuid4()),
        country="FR",
        onboarding_status="active"
    )
    db_session.add(tenant)
    await db_session.flush()
    
    # Créer un utilisateur
    user = User(
        id=uuid4(),
        graph_id=str(uuid4()),
        tenant_client_id=tenant.id,
        user_principal_name="test-fastapi@example.com",
        display_name="Test FastAPI User",
        password_hash=get_password_hash("test-pass-123"),
        account_enabled=True
    )
    db_session.add(user)
    await db_session.flush()
    
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
    db_session.add(analysis)
    await db_session.commit()
    
    # Créer un token
    token = create_access_token(
        data={"sub": str(user.id), "email": user.user_principal_name}
    )
    
    return {
        "user": user,
        "analysis": analysis,
        "token": token,
        "tenant": tenant
    }


@pytest.mark.asyncio
async def test_generate_pdf_report_api(test_user_and_analysis, client: AsyncClient):
    """Test la génération de rapport PDF via l'API"""
    
    test_data = test_user_and_analysis
    analysis_id = test_data["analysis"].id
    token = test_data["token"]
    
    print(f"🚀 Test PDF avec analysis_id: {analysis_id}")
    
    # Appeler l'API
    response = await client.post(
        f"/api/v1/reports/analyses/{analysis_id}/pdf",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"📊 Status: {response.status_code}")
    print(f"📋 Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Rapport PDF créé: {data['id']}")
        print(f"📄 Fichier: {data['file_name']}")
        print(f"📏 Taille: {data['file_size']} bytes")
        
        # Vérifier que le fichier existe
        import os
        if os.path.exists(data['file_path']):
            print(f"✅ Fichier existe: {data['file_path']}")
        else:
            print(f"❌ Fichier manquant: {data['file_path']}")
            
        return True
    else:
        print(f"❌ Échec: {response.status_code} - {response.text}")
        return False


@pytest.mark.asyncio
async def test_generate_excel_report_api(test_user_and_analysis, client: AsyncClient):
    """Test la génération de rapport Excel via l'API"""
    
    test_data = test_user_and_analysis
    analysis_id = test_data["analysis"].id
    token = test_data["token"]
    
    print(f"🚀 Test Excel avec analysis_id: {analysis_id}")
    
    # Appeler l'API
    response = await client.post(
        f"/api/v1/reports/analyses/{analysis_id}/excel",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"📊 Status: {response.status_code}")
    print(f"📋 Response: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Rapport Excel créé: {data['id']}")
        print(f"📄 Fichier: {data['file_name']}")
        print(f"📏 Taille: {data['file_size']} bytes")
        
        # Vérifier que le fichier existe
        import os
        if os.path.exists(data['file_path']):
            print(f"✅ Fichier existe: {data['file_path']}")
        else:
            print(f"❌ Fichier manquant: {data['file_path']}")
            
        return True
    else:
        print(f"❌ Échec: {response.status_code} - {response.text}")
        return False


@pytest.mark.asyncio
async def test_list_reports_api(test_user_and_analysis, client: AsyncClient):
    """Test la liste des reports"""
    
    test_data = test_user_and_analysis
    analysis_id = test_data["analysis"].id
    token = test_data["token"]
    
    print(f"📋 Test liste des reports pour analysis: {analysis_id}")
    
    # Appeler l'API
    response = await client.get(
        f"/api/v1/reports/analyses/{analysis_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Liste récupérée: {data['total']} reports")
        for report in data['reports']:
            print(f"   📄 {report['id']} - {report['report_type']} - {report['file_name']}")
        return True
    else:
        print(f"❌ Échec: {response.status_code} - {response.text}")
        return False


if __name__ == "__main__":
    print("🧪 Test des API de rapport avec FastAPI TestClient")
    # Lancer avec: pytest test_fastapi_reports.py -v -s