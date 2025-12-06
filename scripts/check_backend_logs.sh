#!/bin/bash
# Script pour vérifier les logs du backend et diagnostiquer les erreurs

echo "🔍 Diagnostic des erreurs backend - LOT 12"
echo "================================================"

# Vérifier les conteneurs en cours d'exécution
echo "📦 Conteneurs Docker:"
docker ps | grep -E "(backend|db|redis)"

echo ""
echo "📝 Derniers logs du backend (50 lignes):"
docker-compose logs --tail=50 backend 2>&1

echo ""
echo "🔴 Recherche d'erreurs spécifiques:"
docker-compose logs backend 2>&1 | grep -i -E "(error|exception|traceback|failed)" | tail -20

echo ""
echo "📊 Statut des services:"
make status 2>&1 || docker-compose ps
