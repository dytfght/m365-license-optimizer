# ============================================
# LOT 3 - Script de Validation
# Execute tous les tests et valide le coverage
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LOT 3 - Validation Backend FastAPI" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Change to backend directory
Set-Location -Path ".\backend"

Write-Host "[1/6] Installation des dépendances..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

Write-Host "[2/6] Black - Formatting Check..." -ForegroundColor Yellow
black --check src tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Black check failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Black check passed`n" -ForegroundColor Green

Write-Host "[3/6] Ruff - Linting..." -ForegroundColor Yellow
ruff check src tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ruff check failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Ruff check passed`n" -ForegroundColor Green

Write-Host "[4/6] Mypy - Type Checking..." -ForegroundColor Yellow
mypy src --ignore-missing-imports
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Mypy check failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Mypy check passed`n" -ForegroundColor Green

Write-Host "[5/6] Pytest - Tests Unitaires..." -ForegroundColor Yellow
pytest tests/unit/ -v --cov=src --cov-report=term-missing
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Unit tests failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Unit tests passed`n" -ForegroundColor Green

Write-Host "[6/6] Pytest - Tests Intégration..." -ForegroundColor Yellow
pytest tests/integration/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Integration tests failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Integration tests passed`n" -ForegroundColor Green

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🎉 VALIDATION COMPLÈTE - LOT 3 ✅" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Coverage Report:" -ForegroundColor Yellow
pytest -v --cov=src --cov-report=term-missing --cov-report=html --cov-branch

Write-Host "`nHTML Coverage Report: backend/htmlcov/index.html" -ForegroundColor Cyan

# Return to root
Set-Location -Path ".."

Write-Host "`n✅ Voir LOT3-VALIDATION.md pour le rapport complet" -ForegroundColor Green
