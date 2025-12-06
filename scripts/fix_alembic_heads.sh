#!/bin/bash

# Script pour résoudre les multiples heads d'Alembic après l'ajout du LOT 12

set -e

echo "🔧 Résolution des migrations Alembic - LOT 12"
echo "================================================"

# Aller dans le répertoire backend
cd "$(dirname "$0")/.."
cd backend

echo "📍 Répertoire actuel: $(pwd)"
echo "📂 Contenu du répertoire:"
ls -la alembic.ini 2>/dev/null && echo "✅ alembic.ini trouvé" || echo "❌ alembic.ini manquant"

# Vérifier les heads actuels
echo ""
echo "🔍 Heads actuels:"
alembic heads 2>&1 || echo "Erreur lors de la lecture des heads"

echo ""
echo "📜 Historique:"
alembic history 2>&1 | tail -20 || echo "Erreur lors de la lecture de l'historique"

echo ""
echo "📝 Solution:"
echo "1. Si vous avez plusieurs heads, exécutez:"
echo "   alembic upgrade merge_lot12_i18n_heads"
echo ""
echo "2. Ou fusionnez manuellement avec:"
echo "   alembic merge heads -m 'merge lot12 branches'"
echo ""
echo "3. Puis exécutez:"
echo "   alembic upgrade head"
