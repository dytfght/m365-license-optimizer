#!/bin/bash

echo "🔧 Application de toutes les corrections LOT 12"
echo "================================================"

# Se placer dans le bon répertoire
PROJECT_PATH="/mnt/d/DOC G/Projets/m365-license-optimizer"
cd "$PROJECT_PATH" || { echo "❌ Impossible d'accéder au projet"; exit 1; }

echo "📍 Projet: $PROJECT_PATH"
echo ""

# ÉTAPE 1: Rebuild du backend (résout les problèmes d'imports)
echo "1️⃣ Rebuild Backend (installation des dépendances)..."
docker-compose stop backend
docker-compose build backend
if [ $? -ne 0 ]; then
    echo "❌ Build échoué"
    exit 1
fi
echo "✅ Build terminé"
echo ""

# ÉTAPE 2: Redémarrage des services
echo "2️⃣ Redémarrage des services..."
docker-compose up -d backend
if [ $? -ne 0 ]; then
    echo "❌ Démarrage échoué"
    exit 1
fi
echo "✅ Services redémarrés"
echo ""

# ÉTAPE 3: Attente du démarrage
echo "3️⃣ Attente du démarrage (20s)..."
sleep 20

echo "✅ Backend prêt"
echo ""

# ÉTAPE 4: Vérification des imports
echo "4️⃣ Vérification des imports Python..."
docker-compose exec -T backend python3 -c "
print('Test des imports:')
try:
    from src.services.reports.pdf_generator import PDFGenerator
    print('✅ PDFGenerator importé')
    
    from src.services.reports.excel_generator_simple import ExcelGenerator
    print('✅ ExcelGenerator importé')
    
    from src.services.i18n_service import i18n_service
    print('✅ i18n_service importé')
    
    result = i18n_service.translate('users.not_found', 'fr')
    print(f'✅ Traduction FR: {result}')
    
    result = i18n_service.translate('users.not_found', 'en')
    print(f'✅ Traduction EN: {result}')
    
    print('')
    print('🎉 Tous les modules fonctionnent correctement!')
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Problèmes d'imports détectés"
    exit 1
fi
echo ""

# ÉTAPE 5: Vérification des routes
echo "5️⃣ Vérification des routes API..."
docker-compose exec -T backend python3 -c "
print('Test des routes API:')
try:
    from src.api.v1.endpoints.reports import router as reports_router
    routes = [r for r in reports_router.routes if r.path.endswith('/pdf')]
    if routes:
        print('✅ Route /reports/analyses/{id}/pdf trouvée')
    else:
        print('❌ Route PDF non trouvée')
        exit(1)
    
    from src.api.v1.endpoints.graph import router as graph_router
    routes = [r for r in graph_router.routes if r.path.endswith('/sync_licenses')]
    if routes:
        print('✅ Route /tenants/{id}/sync_licenses trouvée')
    else:
        print('❌ Route sync_licenses non trouvée')
        exit(1)
    
    print('✅ Toutes les routes API sont en place')
except Exception as e:
    print(f'❌ Erreur: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Problèmes de routes API détectés"
    exit 1
fi
echo ""

# ÉTAPE 6: Vérification des logs
echo "6️⃣ Vérification des logs backend (début)..."
sleep 3
docker-compose logs backend --tail=20 2>&1 | grep -i -E "(Ready|Listening|Error|Exception)" | head -10

echo ""
echo "================================================"
echo "✅ Toutes les corrections LOT 12 appliquées!"
echo "================================================"
echo ""
echo "🚀 Prochaines étapes:"
echo ""
echo "1. Rafraîchissez votre navigateur:"
echo "   http://localhost:3001"
echo ""
echo "2. Testez la page i18n:"
echo "   http://localhost:3001/i18n-test"
echo ""
echo "3. Testez la génération de rapports:"
echo "   - Connectez-vous à l'application"
echo "   - Allez dans une analyse"
echo "   - Cliquez sur 'Générer PDF' ou 'Générer Excel'"
echo ""
echo "4. Si des erreurs persistent:"
echo "   cd scripts"
echo "   bash complete_diagnosis.sh"
echo ""
