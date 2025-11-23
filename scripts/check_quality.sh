#!/bin/bash
# Script de vérification qualité et tests pour WSL/Linux
# Usage: ./scripts/check_quality.sh

set -e  # Arrête le script dès qu'une erreur survient

echo "========================================"
echo "🚀 Démarrage des vérifications qualité..."
echo "========================================"

# 1. Imports (isort)
echo -e "\n📦 1. Vérification des imports (isort)..."
isort backend/src backend/tests --check-only --diff
echo "✅ Imports OK"

# 2. Formatage (Black)
echo -e "\n⚫ 2. Vérification du formatage (Black)..."
black backend/src backend/tests --check --diff
echo "✅ Formatage OK"

# 3. Linting (Ruff)
echo -e "\n🧹 3. Linting du code (Ruff)..."
ruff check backend/src backend/tests
echo "✅ Linting OK"

# 4. Typage (Mypy)
echo -e "\ntypes 4. Vérification des types (Mypy)..."
mypy backend/src
echo "✅ Typage OK"

# 5. Tests Unitaires
echo -e "\n🧪 5. Exécution des tests (Pytest)..."
# On définit PYTHONPATH pour que pytest trouve le module src
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
pytest backend/tests -v
echo "✅ Tests OK"

echo -e "\n========================================"
echo "🎉 TOUT EST VERT ! Le code est prêt."
echo "========================================"
