#!/bin/bash

echo "🔍 Diagnostique des erreurs API 422/500"
echo "================================================"

# Configure l'environnement Python
cd "/mnt/d/DOC G/Projets/m365-license-optimizer/backend"

echo "📦 Environnement Python:"
python3 -c "import sys; print(f'Python: {sys.version}')"
python3 -c "import httpx; print(f'httpx: {httpx.__version__}')" 2>/dev/null || echo "httpx n'est pas installé"

echo ""
echo "📝 Lancement des tests API..."
python3 scripts/test_api_endpoints.py || {
    echo ""
    echo "❌ Le test a échoué. Tentative alternative..."
    echo ""
    echo "🔍 Vérification manuelle des endpoints..."
    
    # Tester la santé du backend
    echo ""
    echo "1. Vérification de l'état du backend:"
    curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend non accessible"
    
    # Tester Swagger
    echo ""
    echo "2. Vérification Swagger UI:"
    curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8000/docs
    
    echo ""
    echo "3. Vérification des logs:"
    docker-compose logs backend --tail=30 2>&1 | grep -E "(ERROR|Exception|Traceback)" | head -10
    
    echo ""
    echo "📊 Instructions pour résoudre:"
    echo ""
    echo "A. Résoudre les erreurs 422 (Validation):"
    echo "   - Vérifiez que les données envoyées correspondent aux schémas Pydantic"
    echo "   - Regardez les champs requis dans backend/src/schemas/"
    echo "   - Utilisez Swagger UI pour valider les payloads"
    echo ""
    echo "B. Résoudre les erreurs 500 (Internal Server Error):"
    echo "   1. Arrêtez les services: make down"
    echo "   2. Reconstruisez: make build-all"
    echo "   3. Démarrez: make up"
    echo "   4. Appliquez les migrations: cd backend && alembic upgrade head"
    echo "   5. Vérifiez les logs: docker-compose logs -f backend"
    echo ""
    echo "C. Tester avec Swagger:"
    echo "   - Ouvrez http://localhost:8000/docs"
    echo "   - Authentifiez-vous avec votre token"
    echo "   - Testez les endpoints directement"
    echo ""
    echo "D. Exécuter un test manuel:"
    echo "   cd backend && source venv/bin/activate 2>/dev/null || true"
    echo "   python3 -c \"
import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Test health
        r = await client.get('http://localhost:8000/health')
        print(f'Health: {r.status_code} - {r.text[:100]}')
        
        # Test sync endpoint (sans auth d'abord)
        try:
            r = await client.post('http://localhost:8000/api/v1/tenants/2751a3f3-4c8d-43a2-818a-ec15883379ff/sync_licenses')
            print(f'Sync licenses: {r.status_code}')
            if r.status_code == 401:
                print('   → Auth requise (normal)')
            elif r.status_code == 422:
                print(f'   → Validation error: {r.json()}')
        except Exception as e:
            print(f'   → Exception: {e}')

asyncio.run(test())
\""
}
