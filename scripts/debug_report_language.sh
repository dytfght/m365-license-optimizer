#!/bin/bash

echo "🔍 DIAGNOSTIC - Pourquoi les rapports sont toujours en français ?"
echo "==================================================================="

PROJECT_PATH="/mnt/d/DOC G/Projets/m365-license-optimizer"
cd "$PROJECT_PATH"

# Test 1: Vérifier la langue en base
echo "📊 1. Vérification de la langue de l'utilisateur en base:"
echo "--------------------------------------------------------"
docker-compose exec -T db psql -U admin -d m365_optimizer -c "
SELECT id, user_principal_name, language, email 
FROM optimizer.users 
LIMIT 5;
" 2>/dev/null | grep -E "(id|coq|language|en|fr)"

echo ""
echo "🔍 2. Vérification des logs lors d'une requête de rapport:"
echo "--------------------------------------------------------"

# Vider les logs
docker-compose logs backend > /tmp/logs_before.txt 2>&1

echo "   → Générez un rapport PDF maintenant dans l'interface"
echo "   → Appuyez sur Entrée quand c'est fait..."
read -p ""

echo ""
echo "📜 3. Dernières lignes de log (recherche 'language'):"
echo "---------------------------------------------------"
docker-compose logs backend 2>&1 | grep -B5 -A5 -i "language" | tail -30

echo ""
echo "🔍 4. Vérification de la configuration i18n:"
echo "--------------------------------------------"

echo "   → Configuration du service i18n:"
docker-compose exec -T backend python3 -c "
from src.services.i18n_service import i18n_service
print(f'Langage par défaut du service: {i18n_service.default_language}')
print('Traductions disponibles:', list(i18n_service.all_translations().keys()))
" 2>/dev/null || echo "Impossible de vérifier"

echo ""
echo "🔍 5. Test direct de génération avec langue spécifique:"
echo "------------------------------------------------------"

echo "   → Test avec langue='en' :"
docker-compose exec -T backend python3 -c "
from src.services.i18n_service import i18n_service
i18n_service.set_default_language('en')
print(f'Après set_default_language(en): {i18n_service.default_language}')
result = i18n_service.translate('report.title.pdf')
print(f'translate(report.title.pdf) = {result}')
" 2>/dev/null || echo "Test échoué"

echo ""
echo "   → Test avec langue='fr' :"
docker-compose exec -T backend python3 -c "
from src.services.i18n_service import i18n_service
i18n_service.set_default_language('fr')
print(f'Après set_default_language(fr): {i18n_service.default_language}')
result = i18n_service.translate('report.title.pdf')
print(f'translate(report.title.pdf) = {result}')
" 2>/dev/null || echo "Test échoué"

echo ""
echo "🔍 6. Vérification du code source :"
echo "-----------------------------------"
echo "   → Recherche de 'Accept-Language' dans reports.py:"
grep -n "Accept-Language\|accept_language" backend/src/api/v1/endpoints/reports.py 2>/dev/null || echo "Impossible de lire le fichier"

echo ""
echo "📋 RÉSUMÉ:"
echo "=========="
echo ""
echo "🤔 Pourquoi les rapports sont en français ?"
echo "   → La langue utilisateur depuis la base devrait être utilisée"
echo "   → Mais l'header Accept-Language du navigateur semble prendre le dessus"
echo ""
echo "✅ POUR CORRIGER :"
echo ""
echo "   Option 1: S'assurer que le frontend n'envoie PAS header Accept-Language"
echo "   Option 2: Modifier le backend pour IGNORER l'header"
echo "   Option 3: Modifier la logique : TOUJOURS utiliser current_user.language"
echo ""
echo "🔧 SCRIPT DE CORRECTION :"
echo "   cd scripts DEBUG_LANG_REPORTS.sh"
