#!/bin/bash
# Script de vérification qualité et tests pour WSL/Linux
# Usage: ./scripts/check_quality.sh

set -e  # Arrête le script dès qu'une erreur survient

# Se placer à la racine du projet (parent du dossier scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📂 Working directory: $(pwd)"

# Activation du venv si disponible
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
    echo "✅ Virtual environment activé"
fi

echo "========================================"
echo "🚀 Démarrage des vérifications qualité..."
echo "========================================"

# 1. Imports (isort)
echo -e "\n📦 1. Vérification des imports (isort)..."
python -m isort backend/src backend/tests --check-only --diff
echo "✅ Imports OK"

# 2. Formatage (Black)
echo -e "\n⚫ 2. Vérification du formatage (Black)..."
python -m black backend/src backend/tests --check --diff
echo "✅ Formatage OK"

# 3. Linting (Ruff)
echo -e "\n🧹 3. Linting du code (Ruff)..."
python -m ruff check backend/src backend/tests
echo "✅ Linting OK"

# 4. Typage (Mypy)
echo -e "\n📝 4. Vérification des types (Mypy)..."
python -m mypy backend/src --disable-error-code=import-untyped
echo "✅ Typage OK"

# 5. Tests Unitaires
echo -e "\n🧪 5. Exécution des tests (Pytest)..."
# On définit PYTHONPATH pour que pytest trouve le module src
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
python -m pytest backend/tests -v
echo "✅ Tests OK"

echo -e "\n========================================"
echo "🎉 TOUT EST VERT ! Le code est prêt."
echo "========================================"
