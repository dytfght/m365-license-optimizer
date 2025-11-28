# M365 License Optimizer

## 📋 Vue d'ensemble

M365 License Optimizer est un outil SaaS multitenant permettant aux partenaires Microsoft CSP/MPN d'analyser l'affectation des licences Microsoft 365, l'usage réel des services et d'identifier des opportunités d'optimisation de coûts.

## 🚀 Démarrage rapide

### Prérequis
- Docker Desktop (version 20.10+)
- Docker Compose (version 1.29+)
- Git
- 8GB RAM minimum

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/votre-utilisateur/m365-license-optimizer.git
cd m365-license-optimizer

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos mots de passe (POSTGRES_PASSWORD, REDIS_PASSWORD, PGADMIN_PASSWORD)

# 3. Démarrer les services
docker-compose up -d

# 4. Vérifier l'installation
docker-compose ps
```

Les services devraient être visibles sur :
- PostgreSQL : `localhost:5432`
- Redis : `localhost:6379`
- PgAdmin : `http://localhost:5050`

### Backend API

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

## 🏗️ Architecture

### Stack technique
- **Backend**: FastAPI 0.104.1 + Python 3.12
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0 (async)
- **Cache**: Redis 7 + aioredis
- **Auth**: JWT (HS256) + OAuth2 Password Flow
- **Container**: Docker + Docker Compose
- **Tests**: pytest (≥95% coverage)

### Structure du projet
```
m365-license-optimizer/
├── backend/              # API FastAPI
│   ├── src/api/         # Endpoints REST
│   ├── src/models/      # SQLAlchemy models
│   ├── src/services/    # Business logic
│   └── tests/           # Tests unitaires & intégration
├── docker/              # Configurations Docker
├── scripts/             # Scripts utilitaires
└── docker-compose.yml   # Orchestration des services
```

## 📊 État d'avancement

### ✅ Lots complétés
| Lot | Description | Status |
|-----|-------------|--------|
| **1** | Infrastructure Docker | ✅ Terminé |
| **2** | Modèle de données PostgreSQL | ✅ Terminé |
| **3** | Backend API FastAPI | ✅ Terminé |
| **4** | Microsoft Graph Integration | ✅ Terminé |
| **5** | Partner Center Integration | ✅ Terminé |
| **6** | Optimisation des licences | ✅ Terminé |

### 🎯 Fonctionnalités principales

#### Authentification & Gestion des tenants
```
POST /api/v1/auth/login          # Connexion (JWT)
GET  /api/v1/tenants             # Liste des tenants
```

#### Microsoft Graph Integration
```
POST /api/v1/tenants/{id}/sync_users     # Sync utilisateurs
POST /api/v1/tenants/{id}/sync_licenses  # Sync licences
POST /api/v1/tenants/{id}/sync_usage     # Sync usage metrics
```

#### Partner Center Integration
```
POST /api/v1/pricing/import        # Import prix CSV
GET  /api/v1/pricing/products      # Catalogue produits
GET  /api/v1/pricing/prices/current # Prix actuels
```

#### License Optimization (Lot 6)
```
POST /api/v1/analyses/tenants/{id}/analyses    # Lancer analyse
GET  /api/v1/analyses/tenants/{id}/analyses    # Liste analyses
GET  /api/v1/analyses/analyses/{id}           # Détails + recommandations
POST /api/v1/analyses/recommendations/{id}/apply # Appliquer recommandation
```

## 🧪 Tests

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

## 📚 Documentation détaillée

Les validations détaillées par lot sont disponibles dans les fichiers :
- [LOT1-VALIDATION.md](./LOT1-VALIDATION.md) - Infrastructure Docker
- [LOT2-VALIDATION.md](./LOT2-VALIDATION.md) - Modèle de données
- [LOT3-VALIDATION.md](./LOT3-VALIDATION.md) - Backend API
- [LOT4-VALIDATION.md](./LOT4-VALIDATION.md) - Microsoft Graph
- [LOT5-VALIDATION.md](./LOT5-VALIDATION.md) - Partner Center
- [LOT6-VALIDATION.md](./LOT6-VALIDATION.md) - License Optimization

## 🤝 Contribution

1. Créez une branche : `git checkout -b feature/nom`
2. Committez : `git commit -m "Description"
3. Pushez : `git push origin feature/nom`
4. Ouvrez une Pull Request

## 📄 Licence

Propriétaire - Tous droits réservés