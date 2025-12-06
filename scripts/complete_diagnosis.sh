#!/bin/bash

echo "🔧 Diagnostic Complet des Erreurs API"
echo "=========================================="

# Variables
BACKEND_PATH="/mnt/d/DOC G/Projets/m365-license-optimizer/backend"
PROJECT_PATH="/mnt/d/DOC G/Projets/m365-license-optimizer"

# Fonction pour exécuter une commande dans le conteneur backend
run_in_backend() {
    docker exec m365_license_optimizer_backend "$@" 2>/dev/null
}

echo "📊 ÉTAPE 1: Vérification des conteneurs"
echo "----------------------------------------"
docker ps | grep -E "(m365|backend|redis|postgres)" || echo "❌ Conteneurs non trouvés"

echo ""
echo "📊 ÉTAPE 2: Vérification des logs backend (erreurs récentes)"
echo "--------------------------------------------------------------"
docker-compose logs --tail=100 backend 2>&1 | grep -n -A5 -B5 -E "(ERROR|Exception|422|500|sync_licenses|sync_usage|report)" | head -60

echo ""
echo "📊 ÉTAPE 3: Tester directement depuis le conteneur backend"
echo "-----------------------------------------------------------"
echo "🧪 Test 1: Curl sur l'endpoint health"
docker-compose exec -T backend curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ Health check failed"

echo ""
echo "🧪 Test 2: Vérifier les imports Python"
docker-compose exec -T backend python3 -c "
import sys
print(f'Python version: {sys.version}')

try:
    import structlog
    print('✅ structlog OK')
    
    from src.services.reports.report_service import ReportService
    print('✅ ReportService OK')
    
    from src.services.i18n_service import i18n_service
    print('✅ i18n_service OK')
    
    result = i18n_service.translate('users.not_found', 'fr')
    print(f'✅ Translation test: {result}')
    
    from babel.dates import format_datetime
    from datetime import datetime
    result = format_datetime(datetime.now(), locale='fr_FR')
    print(f'✅ Babel OK: {result[:30]}...')
    
    print('')
    print('🎉 Tous les imports fonctionnent dans le conteneur!')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "🧪 Test 3: Vérifier les migrations"
docker-compose exec -T backend alembic current

echo ""
echo "🧪 Test 4: Tester l'endpoint sync_licenses avec un faux token"
docker-compose exec -T backend bash -c "
cat > /tmp/test_sync.py << 'EOF'
import httpx
import asyncio
import json

async def test():
    async with httpx.AsyncClient() as client:
        # Test sans auth (devrait donner 401, pas 422)
        r = await client.post('http://localhost:8000/api/v1/tenants/2751a3f3-4c8d-43a2-818a-ec15883379ff/sync_licenses')
        print(f'Status: {r.status_code}')
        print(f'Response: {r.text[:200]}')
        
        # Si 422, vérifier le body
        if r.status_code == 422:
            try:
                data = r.json()
                print(f'Detail: {json.dumps(data, indent=2)}')
            except:
                print('Cannot parse JSON response')

asyncio.run(test())
EOF
python3 /tmp/test_sync.py
"

echo ""
echo "=========================================="
echo "📈 RÉSUMÉ DES SOLUTIONS"
echo "=========================================="

echo ""
echo "❌ PROBLÈMES IDENTIFIÉS:"
echo ""
echo "1. Erreurs 422 (Validation):"
echo "   → Probablement dû à un format de requête incorrect"
echo "   → OU un problème avec le rate limiter"
echo "   → OU les données dans le body ne correspondent pas au schéma"
echo ""
echo "2. Erreurs 500 (Rapports):"
echo "   → Erreur interne dans le ReportService"
echo "   → Manque de dépendances OU exception non gérée"
echo ""
echo "✅ SOLUTIONS À APPLIQUER:"
echo ""
echo "A. Résoudre les problèmes 422:"
echo "   cd $PROJECT_PATH"
echo "   docker-compose stop backend"
echo "   docker-compose build backend"
echo "   docker-compose up -d backend"
echo ""
echo "B. Résoudre les problèmes 500 (Rapports):"
echo "   cd $BACKEND_PATH"
echo "   docker-compose exec backend pip install --no-cache-dir -r requirements.txt"
echo "   docker-compose restart backend"
echo ""
echo "C. Alternative complète (rebuild):"
echo "   cd $PROJECT_PATH"
echo "   docker-compose down"
echo "   docker-compose up -d --build"
echo "   cd backend"
echo "   docker-compose exec backend alembic upgrade head"
echo ""
echo "D. Vérification finale:"
echo "   cd $PROJECT_PATH"
echo "   docker-compose logs -f backend"
echo "   → Puis retestez les endpoints"

echo ""
echo "📝 NOTES:"
echo "- Tous les tests doivent être exécutés DANS les conteneurs Docker"
echo "- Les modules Python sont installés uniquement dans le conteneur backend"
echo "- Utilisez 'docker-compose exec backend' pour toute commande Python"
echo ""
echo "🔧 Pour tester manuellement:"
echo "   docker-compose exec backend bash"
echo "   → Vous serez dans le conteneur avec tous les modules disponibles"
echo ""
echo "✅ Une fois les corrections appliquées, retournez sur:"
echo "   http://localhost:3001"
echo "   ET testez à nouveau la génération de rapports"
