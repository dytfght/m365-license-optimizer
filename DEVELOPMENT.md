# 🛠️ Guide de Développement

Ce document regroupe les instructions pour le développement, l'installation manuelle et les tests du M365 License Optimizer.

## 🐍 Backend API - Installation Manuelle

Si vous ne souhaitez pas utiliser Docker pour tout :

```bash
# 1. Démarrer l'infrastructure (si pas déjà fait)
docker-compose up -d db redis

# 2. Installer les dépendances Python
cd backend
pip install -r requirements.txt

# 3. Générer la clé de chiffrement (première fois uniquement)
python ../scripts/generate_encryption_key.py
# Copier la clé dans votre .env : ENCRYPTION_KEY=...

# 4. Appliquer les migrations
alembic upgrade head

# 5. Démarrer le serveur
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Tester l'API :
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/version
open http://localhost:8000/docs  # Documentation OpenAPI
```

## 🧪 Tests

### Backend
```bash
cd backend
# Tests unitaires
pytest tests/unit/ -v

# Tests d'intégration
pytest tests/integration/ -v

# Coverage complet
pytest -v --cov=src --cov-report=html

# Qualité de code
black src/ tests/
ruff check src/ tests/
mypy src/
```

### Frontend
```bash
cd frontend
npm test
```

## 🔧 Commandes utiles

### Docker
```bash
docker-compose logs -f          # Logs en temps réel
docker-compose restart          # Redémarrer
docker-compose down -v          # Arrêt + suppression données
```

### Database (Alembic)
```bash
alembic upgrade head            # Appliquer migrations
alembic revision --autogenerate -m "description"  # Nouvelle migration
alembic current                 # Version actuelle
```

## 🌍 Internationalisation (i18n)

Pour ajouter une nouvelle langue ou modifier les traductions existantes, référez-vous à la documentation détaillée :
[LOT12-VALIDATION.md](./LOT12-VALIDATION.md)
