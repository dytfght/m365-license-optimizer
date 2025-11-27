# M365 License Optimizer

## 📋 Vue d'ensemble

M365 License Optimizer est un outil SaaS multitenant permettant aux partenaires Microsoft CSP/MPN d'analyser l'affectation des licences Microsoft 365, l'usage réel des services et d'identifier des opportunités d'optimisation de coûts.

## 🚀 Setup Environnement Local

### Prérequis

- Docker Desktop (version 20.10 ou supérieure)
- Docker Compose (version 1.29 ou supérieure)
- Git
- 8GB RAM minimum recommandés
- Outils optionnels :
  - `psql` (client PostgreSQL)
  - `redis-cli` (client Redis)

### Installation

#### 1. Cloner le repository

```bash
git clone https://github.com/votre-utilisateur/m365-license-optimizer.git
cd m365-license-optimizer
```

#### 2. Configuration des variables d'environnement

Copiez le fichier d'exemple et configurez vos variables :

```bash
cp .env.example .env
```

Éditez le fichier `.env` et modifiez **au minimum** :
- `POSTGRES_PASSWORD` : Mot de passe PostgreSQL (minimum 12 caractères)
- `REDIS_PASSWORD` : Mot de passe Redis (minimum 12 caractères)
- `PGADMIN_PASSWORD` : Mot de passe PgAdmin (minimum 8 caractères)

⚠️ **IMPORTANT** : Ne commitez JAMAIS le fichier `.env` dans Git !

#### 3. Démarrage des services

Lancez tous les services avec Docker Compose :

```bash
docker-compose up -d
```

Vérifiez que les services sont démarrés :

```bash
docker-compose ps
```

Vous devriez voir 3 conteneurs en statut "Up" :
- `m365_optimizer_db` (PostgreSQL)
- `m365_optimizer_redis` (Redis)
- `m365_optimizer_pgadmin` (PgAdmin - interface web optionnelle)

#### 4. Vérification de l'installation

##### PostgreSQL

Testez la connexion à PostgreSQL :

```bash
# Via psql
psql -h localhost -p 5432 -U admin -d m365_optimizer

# Ou via Docker exec
docker exec -it m365_optimizer_db psql -U admin -d m365_optimizer
```

Commandes de vérification :
```sql
-- Afficher les schémas
\dn

-- Lister les tables
\dt optimizer.*

-- Vérifier les données de test
SELECT * FROM optimizer.tenant_clients;

-- Quitter
\q
```

##### Redis

Testez la connexion à Redis :

```bash
# Via redis-cli (remplacez PASSWORD par votre REDIS_PASSWORD)
redis-cli -h localhost -p 6379 -a PASSWORD

# Ou via Docker exec
docker exec -it m365_optimizer_redis redis-cli -a PASSWORD
```

Commandes de vérification :
```bash
# Test de connexion
PING
# Réponse attendue : PONG

# Vérifier la configuration
CONFIG GET maxmemory-policy
# Réponse attendue : allkeys-lru

# Quitter
exit
```

##### PgAdmin (Interface Web)

Accédez à PgAdmin via votre navigateur :

```
http://localhost:5050
```

Identifiants (depuis votre .env) :
- Email : `admin@m365optimizer.local`
- Password : Votre `PGADMIN_PASSWORD`

Pour connecter PgAdmin à PostgreSQL :
1. Clic droit sur "Servers" → "Register" → "Server"
2. General tab :
   - Name : `M365 Optimizer Local`
3. Connection tab :
   - Host : `db` (nom du service Docker)
   - Port : `5432`
   - Database : `m365_optimizer`
   - Username : `admin`
   - Password : Votre `POSTGRES_PASSWORD`
4. Save

#### 5. Test de persistence des données

Vérifiez que les données persistent après redémarrage :

```bash
# Ajoutez une donnée de test
docker exec -it m365_optimizer_db psql -U admin -d m365_optimizer -c "INSERT INTO optimizer.tenant_clients (tenant_id, name, country) VALUES ('test-persistence', 'Test Corp', 'FR');"

# Arrêtez les conteneurs
docker-compose down

# Redémarrez
docker-compose up -d

# Vérifiez que la donnée existe toujours
docker exec -it m365_optimizer_db psql -U admin -d m365_optimizer -c "SELECT name FROM optimizer.tenant_clients WHERE tenant_id = 'test-persistence';"
```

### Arrêt des services

```bash
# Arrêter les conteneurs (conserve les volumes/données)
docker-compose down

# Arrêter ET supprimer les volumes (⚠️ perte de données)
docker-compose down -v
```

### Nettoyage complet

```bash
# Supprimer conteneurs, volumes, réseaux et images
docker-compose down -v --rmi all
```

## 🔧 Commandes utiles

### Logs

```bash
# Voir tous les logs
docker-compose logs

# Suivre les logs en temps réel
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs db
docker-compose logs redis
```

### Redémarrage

```bash
# Redémarrer tous les services
docker-compose restart

# Redémarrer un service spécifique
docker-compose restart db
```

### Mise à jour après modification de init.sql

Si vous modifiez `docker/db/init.sql`, vous devez recréer la base :

```bash
docker-compose down -v
docker-compose up -d
```

## 🏗️ Structure du projet

```
m365-license-optimizer/
├── backend/
│   ├── src/
│   │   ├── api/v1/endpoints/    # Endpoints REST (auth, tenants, health)
│   │   ├── core/                # Config, security, database, logging, middleware
│   │   ├── models/              # SQLAlchemy models (schéma optimizer)
│   │   ├── repositories/        # Repository pattern (base, tenant, user)
│   │   ├── schemas/             # Pydantic models
│   │   └── services/            # Business logic (auth_service)
│   ├── tests/
│   │   ├── unit/                # Tests unitaires (≥95% coverage)
│   │   └── integration/         # Tests d'intégration API
│   ├── alembic/                 # Migrations de base de données
│   ├── Dockerfile               # Multi-stage build optimisé
│   └── requirements.txt         # Dépendances Python
├── docker/
│   └── db/
│       └── init.sql             # Script d'initialisation PostgreSQL
├── .github/
│   └── workflows/
│       ├── deploy-azure.yml     # Déploiement Azure
│       └── tests-backend.yml    # CI/CD (lint, test, build)
├── docker-compose.yml           # Configuration Docker Compose
├── .env                         # Variables d'environnement (non versionné)
├── .env.example                 # Template des variables d'environnement
├── .gitignore                   # Fichiers à ignorer par Git
├── README.md                    # Ce fichier
├── LOT1-VALIDATION.md           # Validation infrastructure Docker
├── LOT2-VALIDATION.md           # Validation modèle de données
├── LOT3-VALIDATION.md           # Validation backend API
├── LOT4-VALIDATION.md           # Validation Microsoft Graph
└── LOT5-VALIDATION.md           # Validation Partner Center
```

## 🛠️ Architecture Backend (Lot 3)

### Stack Technique
- **Framework** : FastAPI 0.104.1
- **Database** : PostgreSQL 15 + SQLAlchemy 2.0 (AsyncSession)
- **Cache** : Redis 7 + aioredis
- **Auth** : JWT (HS256) + OAuth2 Password Flow
- **Logging** : structlog (format JSON)
- **Tests** : pytest + coverage (≥95%)
- **Docker** : Multi-stage build (~450MB)

### Endpoints Principaux (Lots 3)
```
GET  /health                    # Health check basique
GET  /api/v1/health             # Health check détaillé (DB + Redis)
GET  /api/v1/version            # Version de l'API
POST /api/v1/auth/login         # Authentification (access + refresh tokens)
POST /api/v1/auth/refresh       # Renouvellement du token
GET  /api/v1/tenants            # Liste des tenants (protégé)
```

### Middleware
- **Rate Limiting** : 100 req/min, 1000 req/jour (slowapi + Redis)
- **Security Headers** : X-Frame-Options, CSP, HSTS, X-Content-Type-Options
- **Request ID** : UUID pour traçabilité
- **Audit Logging** : Logs de toutes les requêtes avec timing
- **Transaction Management** : Gestion automatique des transactions DB

### Accès à l'API
- **Base URL** : `http://localhost:8000`
- **Documentation OpenAPI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`


## 🔗 Architecture Microsoft Graph (Lot 4)

### Stack Technique
- **MSAL** : Microsoft Authentication Library 1.31.1
- **Chiffrement** : Fernet (cryptography 42.0.2)
- **Cache tokens** : Redis avec TTL intelligent (expiry - 5min)
- **Retry logic** : Exponential backoff sur 429/5xx
- **Pagination** : Support @odata.nextLink automatique

### Endpoints Microsoft Graph (Lot 4)
```
POST /api/v1/tenants/{tenant_id}/sync_users     # Synchronisation utilisateurs Graph
POST /api/v1/tenants/{tenant_id}/sync_licenses  # Synchronisation licences Graph
POST /api/v1/tenants/{tenant_id}/sync_usage     # Synchronisation rapports d'usage
```

**Note** : Ces endpoints nécessitent :
- JWT authentication (Bearer token)
- Rate limiting : 1 requête/minute par endpoint
- Credentials Microsoft Graph configurés dans la table `tenant_app_registrations`

### Services Implémentés
- `EncryptionService` : Chiffrement/déchiffrement des secrets clients (Fernet)
- `GraphAuthService` : Acquisition et cache des tokens MSAL
- `GraphService` : Collecte données depuis Microsoft Graph API
  - `/users` : Informations utilisateurs
  - `/subscribedSkus` : Licences souscrites
  - `/users/{id}/licenseDetails` : Détails licences par utilisateur
  - Rapports d'usage : Email, OneDrive, SharePoint, Teams (CSV parsing)


## 🏢 Architecture Partner Center (Lot 5)

### Stack Technique
- **MSAL** : Client credentials flow (Partner Center API)
- **Cache** : Redis pour pricing (TTL 24h) et tokens
- **Import** : Streaming CSV parsing (aiofiles)
- **Models** : `MicrosoftProduct` (Catalog) et `MicrosoftPrice` (Pricing)

### Endpoints Partner Center (Lot 5)
```
POST /api/v1/pricing/import                 # Import CSV catalogue prix
GET  /api/v1/pricing/products               # Recherche produits
GET  /api/v1/pricing/products/{id}/{sku}    # Détails produit
GET  /api/v1/pricing/prices/current         # Prix effectif actuel
```

### Services Implémentés
- `PartnerAuthService` : Authentification MSAL spécifique Partner Center
- `PartnerService` : Client API (Pricing, Subscriptions) avec retry logic
- `PriceImportService` : Import asynchrone performant de fichiers CSV volumineux
- `ProductRepository` / `PriceRepository` : Gestion optimisée des données pricing


## 📊 Architecture Optimisation de Licences (Lot 6)

### Stack Technique
- **Algorithmes** : Analyse d'usage sur 28 jours (Graph API data)
- **Pricing** : Calculs économies basés sur Partner Center pricing
- **Models** : `Analysis` (summary JSONB), `Recommendation` (savings calculation)
- **Logique** : Détection inactifs, downgrade suggestions, ROI calculation

### Endpoints Optimisation (Lot 6)
```
POST /api/v1/analyses/tenants/{tenant_id}/analyses    # Lancer analyse (rate limit 1/min)
GET  /api/v1/analyses/tenants/{tenant_id}/analyses    # Lister analyses
GET  /api/v1/analyses/analyses/{analysis_id}          # Détails avec recommendations
POST /api/v1/analyses/recommendations/{id}/apply      # Accepter/rejeter recommendation
```

### Services Implémentés
- `AnalysisService` : Analyse d'usage → recommandations (400+ lignes de logique)
  - `run_analysis(tenant_id)` : Algorithme complet d'optimisation
  - `_calculate_usage_scores()` : Calcul scores par service (Exchange, Teams, etc.)
  - `_generate_recommendation()` : Génération recommandations avec savings
- `RecommendationService` : Gestion cycle de vie des recommandations (apply/reject)
- `AnalysisRepository` / `RecommendationRepository` : Accès données avec bulk insert

### Algorithmes d'Optimisation
- **Détection inactifs** : Users sans activité >90j → Remove license
- **Downgrade E5→E3** : Pas d'usage Advanced Analytics/Power BI → Économie 30%
- **Downgrade E3→E1** : Pas d'Office desktop → Économie 40%
- **Downgrade E1/E3→F3** : Usage minimal (frontline workers) → Économie 50%
- **Calcul ROI** : Savings mensuel + projection annuelle


## ✅ Critères d'acceptation

### Lot 1 - Infrastructure Docker (✅ COMPLET)

- [x] PostgreSQL 15 accessible sur le port 5432
- [x] Redis 7 accessible sur le port 6379
- [x] Volumes persistants pour PostgreSQL et Redis
- [x] Script init.sql exécuté au premier démarrage
- [x] Configuration Redis avec `maxmemory-policy allkeys-lru`
- [x] Authentification par mot de passe pour PostgreSQL et Redis
- [x] Schéma `optimizer` créé avec tables de base
- [x] Utilisateur `readonly` créé pour audits futurs
- [x] Données de test insérées et persistantes après redémarrage
- [x] Documentation complète dans README.md
- [x] Fichier .env.example fourni
- [x] PgAdmin optionnel pour interface graphique

### Lot 2 - Modèle de Données PostgreSQL (✅ VALIDÉ)

- [x] 10 tables principales créées dans le schéma `optimizer`
- [x] Migrations Alembic fonctionnelles (`upgrade`/`downgrade`)
- [x] Relations foreign keys avec CASCADE approprié
- [x] Index sur colonnes critiques (tenant_id, user_id, report_date)
- [x] Contraintes UNIQUE (graph_id, sku_part_number, etc.)
- [x] Types Enum pour statuts et catégories
- [x] Colonnes JSONB pour données semi-structurées
- [x] Scripts de seed data (2 tenants de test)
- [x] SkuServiceMatrix avec 15 SKU principales
- [x] Tests d'intégrité FK et UNIQUE
- [x] Tests de performance (\<50ms)
- [x] Documentation ERD et mapping tables

### Lot 3 - Backend FastAPI (✅ COMPLETED)

- [x] Architecture Repository Pattern complète
- [x] Authentification JWT (access + refresh tokens)
- [x] Endpoints obligatoires (/health, /version, /auth, /tenants)
- [x] Middleware complet (rate limiting, security headers, audit, transaction)
- [x] Logging structuré JSON (structlog)
- [x] Rate limiting (100 req/min, 1000 req/jour)
- [x] Security headers (X-Frame-Options, CSP, HSTS, etc.)
- [x] Dockerfile multi-stage optimisé (~450MB vs ~800MB)
- [x] Tests unitaires et d'intégration (coverage ≥ 95%)

### Lot 4 - Microsoft Graph Integration (✅ COMPLET)

- [x] EncryptionService avec Fernet pour secrets clients
- [x] GraphAuthService avec MSAL (client credentials flow)
- [x] Cache Redis des tokens avec TTL intelligent
- [x] GraphService pour collecte données (users, licenses, usage)
- [x] Endpoints API pour synchronisation (/sync_users, /sync_licenses, /sync_usage)
- [x] Gestion pagination, retry logic, rate limiting
- [x] Repositories avec upsert pour éviter doublons
- [x] Modèle UsageMetrics + schemas Pydantic
- [x] Configuration ENCRYPTION_KEY dans .env
- [x] Tests unitaires créés (49 tests - 4 fichiers)
- [x] CI/CD GitHub Actions (lint, test, build)
- [x] Documentation OpenAPI complète (/docs, /redoc)

### Lot 5 - Partner Center Integration (✅ COMPLET)

- [x] Tables `microsoft_products` et `microsoft_prices` créées
- [x] PartnerAuthService avec MSAL et cache Redis
- [x] PartnerService pour fetch pricing et subscriptions
- [x] PriceImportService pour import CSV performant
- [x] Endpoints API d'import et de consultation
- [x] Gestion des erreurs et retry logic (429, 5xx)
- [x] Tests unitaires et d'intégration (42 tests)
- [x] Documentation OpenAPI mise à jour
- [x] Validation manuelle de l'import CSV (17k+ prix)

### Lot 6 - License Optimization Analysis (✅ COMPLET)

- [x] Tables `analyses` et `recommendations` créées
- [x] Migrations Alembic fonctionnelles (upgrade/downgrade)
- [x] AnalysisRepository avec CRUD et queries optimisées  
- [x] RecommendationRepository avec bulk insert
- [x] AnalysisService avec algorithmes d'optimisation
  - [x] Calcul usage scores (Exchange, OneDrive, SharePoint, Teams, Office)
  - [x] Détection utilisateurs inactifs (>90j)
  - [x] Recommandations downgrade (E5→E3, E3→E1, etc.)
  - [x] Calcul savings mensuels/annuels
- [x] RecommendationService (apply/reject)
- [x] Endpoints API (/analyses, /recommendations)
- [x] JWT authentication + rate limiting (1 req/min)
- [x] Tenant isolation et authorization checks
- [x] Tests unitaires (10) + intégration (12) = 22 tests
- [x] Coverage ≥95% sur nouveaux modules
- [x] Documentation et validation (LOT6-VALIDATION.md)

## 🐛 Dépannage

### Erreur : "port already allocated"

Un autre service utilise le port 5432 ou 6379. Modifiez les ports dans `docker-compose.yml` :

```yaml
ports:
  - '5433:5432'  # Pour PostgreSQL
  - '6380:6379'  # Pour Redis
```

### Erreur : "permission denied" sur init.sql

Assurez-vous que le fichier a les bonnes permissions :

```bash
chmod 644 docker/db/init.sql
```

### Redis n'accepte pas les connexions

Vérifiez que vous utilisez le bon mot de passe :

```bash
docker exec -it m365_optimizer_redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2)
```

### Reset complet de la base de données

```bash
docker-compose down -v
docker volume rm m365-license-optimizer_postgres_data
docker-compose up -d
```

## 🔬 Backend - Démarrage et Tests

### Démarrage du Backend (Lots 3 & 4)

```bash
# 1. Démarrer l'infrastructure (DB + Redis)
docker-compose up -d db redis

# 2. Installer les dépendances Python
cd backend
pip install -r requirements.txt

# 3. Générer la clé de chiffrement (LOT4 - première fois uniquement)
python ../scripts/generate_encryption_key.py
# Copier la clé générée dans votre .env : ENCRYPTION_KEY=...

# 4. Appliquer les migrations Alembic
alembic upgrade head

# 5. Démarrer le serveur FastAPI
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Ou tout démarrer avec Docker Compose
docker-compose up -d
```

**⚠️ Important pour LOT4** :
- La variable `ENCRYPTION_KEY` est **obligatoire** pour le chiffrement des secrets clients Microsoft Graph
- Générez-la avec `python scripts/generate_encryption_key.py` ou via Python :
  ```python
  from cryptography.fernet import Fernet
  print(Fernet.generate_key().decode())
  ```

### Tester l'API

```bash
# Health check basique
curl http://localhost:8000/health

# Health check détaillé
curl http://localhost:8000/api/v1/health

# Version de l'API
curl http://localhost:8000/api/v1/version

# Documentation interactive
open http://localhost:8000/docs
```

### Tests Backend

```bash
cd backend

# Tests unitaires
pytest tests/unit/ -v

# Tests d'intégration
pytest tests/integration/ -v

# Tous les tests avec coverage
pytest -v --cov=src --cov-report=term-missing --cov-report=html

# Linting et formatage
black src/ tests/
ruff check src/ tests/
mypy src/
```

### Commandes Alembic

```bash
cd backend

# Appliquer toutes les migrations
alembic upgrade head

# Revenir à une version précédente
alembic downgrade -1

# Afficher l'historique des migrations
alembic history

# Créer une nouvelle migration
alembic revision --autogenerate -m "description"

# Vérifier la version actuelle
alembic current
```

## 📚 État d'avancement du projet

### ✅ Lots Complétés

#### ✅ Lot 1 : Infrastructure Docker & PostgreSQL
- Configuration Docker Compose complète
- PostgreSQL 15 avec schéma `optimizer`
- Redis 7 avec authentification
- PgAdmin 4 pour la gestion de la base
- Scripts d'initialisation SQL
- **Validation** : [LOT1-VALIDATION.md](./LOT1-VALIDATION.md)

#### ✅ Lot 2 : Modèle de Données
- Schéma complet avec 5 tables (tenants, users, licenses, usage, app registrations)
- Migrations Alembic versionnées
- Relations et contraintes FK
- Données de test automatiques
- **Validation** : [LOT2-VALIDATION.md](./LOT2-VALIDATION.md)

#### ✅ Lot 3 : API Backend FastAPI
- API REST avec FastAPI 0.104.1
- Authentication JWT stateless
- Repository pattern (dependency injection)
- Middleware : RequestID, Security Headers, Transaction, AuditLog, CORS
- Logging structuré (JSON)
- Tests unitaires + intégration (99% coverage)
- Build Docker multi-stage optimisé
- **Validation** : [LOT3-VALIDATION.md](./LOT3-VALIDATION.md)

#### ✅ Lot 4 : Microsoft Graph Integration
- `GraphAuthService` (MSAL avec cache Redis)
- `GraphService` (Users, Licenses, Usage)
- `EncryptionService` (Fernet pour secrets)
- Endpoints `/api/v1/graph/sync/licenses` et `/usage`
- Tests unitaires et d'intégration
- **Validation** : [LOT4-VALIDATION.md](./LOT4-VALIDATION.md)

#### ✅ Lot 5 : Partner Center Integration
- Modèles `microsoft_products` (1,058) et `microsoft_prices` (17,863)
- `PartnerAuthService` (MSAL + Redis cache)
- `PartnerService` (fetch_pricing, fetch_subscriptions)
- `PriceImportService` (CSV import avec déduplication)
- Repositories: ProductRepository, PriceRepository (upsert_bulk)
- Endpoints API: `/api/v1/pricing/import`, `/products`, `/prices/current`
- Tests unitaires (31) + intégration (11) = 42 tests
- **Validation** : [LOT5-VALIDATION.md](./LOT5-VALIDATION.md)

#### ✅ Lot 6 : Optimisation des Licences Basée sur l'Utilisation (COMPLET)
- Tables `analyses` et `recommendations` avec migrations Alembic
- `AnalysisService` avec algorithmes d'optimisation intelligents
- Détection utilisateurs inactifs (>90j sans activité)
- Recommandations de downgrade (E5→E3, E3→E1, E1→F3)
- Calcul économies potentielles (mensuelles/annuelles)
- Endpoints API : POST/GET analyses, GET détails, POST apply recommendation
- Tests unitaires (10) + intégration (12) = 22 tests
- **Validation** : [LOT6-VALIDATION.md](./LOT6-VALIDATION.md)

#### Lot 7 : Rapports PDF/Excel (À venir)

### 📊 Vue d'ensemble
| Lot | Description | Status | Progression |
|-----|-------------|--------|-------------|
| **1** | Infrastructure Docker | ✅ Terminé | 100% |
| **2** | Modèle de données PostgreSQL | ✅ Terminé | 100% |
| **3** | Backend API FastAPI | ✅ Terminé | 100% |
| **4** | Microsoft Graph Integration | ✅ Terminé | 100% |
| **5** | Partner Center Integration | ✅ Terminé | 100% |
| **6** | Optimisation Licences (Usage Analysis) | ✅ Terminé | 100% |
| **7** | Rapports PDF/Excel | ⬜ À venir | 0% |
| **8** | Frontend React | ⬜ À venir | 0% |
| **9-18** | Fonctionnalités avancées | ⬜ À venir | 0% |

### Lots Terminés ✅
- **Lot 1** : Infrastructure locale Docker (PostgreSQL 15 + Redis 7 + PgAdmin)
- **Lot 2** : Modèle de données complet avec migrations Alembic (10 tables, indexes, FK)
- **Lot 3** : Backend API FastAPI avec JWT, middleware, tests (≥95% coverage) et CI/CD
- **Lot 4** : Intégration Microsoft Graph avec EncryptionService, GraphAuthService, GraphService, endpoints sync, et 49 tests
- **Lot 5** : Intégration Microsoft Partner Center avec import CSV, pricing, subscriptions et 42 tests
- **Lot 6** : Optimisation licences avec analyses d'usage, recommandations, calculs savings et 22 tests

### Lots en Cours / À Venir 🚧
- **Lot 7** : Rapports PDF/Excel
- **Lot 8** : Frontend React
- **Lot 9-18** : Fonctionnalités avancées

## 🤝 Contribution

Pour contribuer au projet :

1. Créez une branche : `git checkout -b feature/ma-fonctionnalite`
2. Committez vos changements : `git commit -m "Ajout fonctionnalité X"`
3. Pushez la branche : `git push origin feature/ma-fonctionnalite`
4. Ouvrez une Pull Request

## 📄 Licence

Propriétaire - Tous droits réservés

## 📞 Support

Pour toute question, contactez l'équipe de développement.
