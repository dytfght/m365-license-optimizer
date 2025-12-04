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
- Frontend : `http://localhost:3000`
- Backend API : `http://localhost:8000`
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
- **Frontend**: React 18 + Next.js 14 (Pages Router) + TypeScript
- **Styling**: Tailwind CSS
- **State/Data**: React Query + Context API
- **Backend**: FastAPI 0.104.1 + Python 3.12
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0 (async)
- **Cache**: Redis 7 + aioredis
- **Auth**: JWT (HS256) + OAuth2 Password Flow
- **Container**: Docker + Docker Compose
- **Tests**: pytest (backend), Jest (frontend)

### Structure du projet
```
m365-license-optimizer/
├── backend/              # API FastAPI
│   ├── src/api/         # Endpoints REST
│   ├── src/models/      # SQLAlchemy models
│   ├── src/services/    # Business logic
│   └── tests/           # Tests unitaires & intégration
├── frontend/             # Frontend React/Next.js (Lot 9)
│   ├── src/components/  # UI Components
│   ├── src/pages/       # Routes
│   └── src/services/    # API integration
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
| **7** | Génération de rapports PDF/Excel | ✅ Terminé |
| **8** | Partner Center Mapping & Add-ons | ✅ Terminé |
| **9** | Frontend React/Next.js | ✅ Terminé |
| **10** | Sécurité, RGPD & Journalisation | ✅ Terminé |

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

#### Report Generation (Lot 7)
```
POST /api/v1/reports/analyses/{id}/pdf         # Générer rapport PDF
POST /api/v1/reports/analyses/{id}/excel       # Générer rapport Excel
GET  /api/v1/reports/analyses/{id}             # Liste rapports d'une analyse
GET  /api/v1/reports/tenants/{id}              # Liste rapports d'un tenant
GET  /api/v1/reports/{id}                      # Détails d'un rapport
GET  /api/v1/reports/{id}/download             # Info de téléchargement
GET  /api/v1/reports/{id}/file                 # Télécharger le fichier
DELETE /api/v1/reports/{id}                    # Supprimer un rapport
POST /api/v1/reports/cleanup                   # Nettoyer rapports expirés
```

#### SKU Mapping & Add-ons (Lot 8)
```
GET    /api/v1/admin/sku-mapping/summary                          # Statistiques mappings
POST   /api/v1/admin/sku-mapping/sync/products                    # Sync produits Partner Center
POST   /api/v1/admin/sku-mapping/sync/compatibility               # Sync règles compatibilité
GET    /api/v1/admin/sku-mapping/compatible-addons/{base_sku_id}  # Add-ons compatibles
POST   /api/v1/admin/sku-mapping/validate-addon                   # Valider compatibilité
GET    /api/v1/admin/sku-mapping/compatibility-mappings           # Liste mappings
POST   /api/v1/admin/sku-mapping/compatibility-mappings           # Créer mapping
PUT    /api/v1/admin/sku-mapping/compatibility-mappings/{id}      # Modifier mapping
DELETE /api/v1/admin/sku-mapping/compatibility-mappings/{id}      # Supprimer mapping
GET    /api/v1/admin/sku-mapping/recommendations/{base_sku_id}    # Recommandations add-ons
```

#### Sécurité, RGPD & Logs (Lot 10)
```
POST   /api/v1/gdpr/consent/{tenant_id}     # Enregistrer consent
GET    /api/v1/gdpr/consent/{tenant_id}     # Vérifier consent
GET    /api/v1/gdpr/export/{user_id}        # Export données (Art 20)
DELETE /api/v1/gdpr/delete/{user_id}        # Droit à l'oubli (Art 17)
POST   /api/v1/gdpr/admin/registry          # PDF registre (Art 30)
GET    /api/v1/admin/logs                   # Liste logs filtrée
GET    /api/v1/admin/logs/{id}              # Détails log
POST   /api/v1/admin/logs/purge             # Purge RGPD (90j)
GET    /api/v1/admin/logs/statistics/summary # Stats erreurs
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
- [LOT7-VALIDATION.md](./LOT7-VALIDATION.md) - Report Generation
- [LOT8-VALIDATION.md](./LOT8-VALIDATION.md) - Partner Center Mapping & Add-ons
- [LOT10-VALIDATION.md](./LOT10-VALIDATION.md) - Sécurité, RGPD & Journalisation

## 🤝 Contribution

1. Créez une branche : `git checkout -b feature/nom`
2. Committez : `git commit -m "Description"
3. Pushez : `git push origin feature/nom`
4. Ouvrez une Pull Request

## 📄 Licence

Propriétaire - Tous droits réservés