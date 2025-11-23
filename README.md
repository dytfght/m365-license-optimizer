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
└── LOT3-VALIDATION.md           # Validation backend API
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

### Endpoints Principaux
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
- [x] CI/CD GitHub Actions (lint, test, build)
- [x] Documentation OpenAPI complète (/docs, /redoc)

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

### Démarrage du Backend (Lot 3)

```bash
# 1. Démarrer l'infrastructure (DB + Redis)
docker-compose up -d db redis

# 2. Installer les dépendances Python
cd backend
pip install -r requirements.txt

# 3. Appliquer les migrations Alembic
alembic upgrade head

# 4. Démarrer le serveur FastAPI
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Ou tout démarrer avec Docker Compose
docker-compose up -d
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

## 📚 Prochaines étapes

### Lots Terminés ✅
- **Lot 1** : Infrastructure locale Docker (PostgreSQL + Redis)
- **Lot 2** : Modèle de données complet avec migrations Alembic
- **Lot 3** : Backend API FastAPI avec JWT, middleware, tests et CI/CD

### Lots en Cours / À Venir 🚧
- **Lot 4** : Intégration Microsoft Graph (auth, users, licenses)
- **Lot 5** : Intégration Microsoft Partner Center (pricing, subscriptions)
- **Lot 6** : Jobs de synchronisation automatique
- **Lot 7** : Frontend React
- **Lot 8-18** : Fonctionnalités avancées (algorithmes ML, reporting, sécurité, déploiement Azure)

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
