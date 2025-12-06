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
# Éditer .env avec vos mots de passe

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

> [!TIP]
> Pour une installation manuelle (sans Docker), ou pour lancer les tests, consultez le [Guide de Développement](./DEVELOPMENT.md).

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
| **11** | Déploiement, Exploitation & Observabilité | ✅ Terminé |
| **12** | Internationalisation (i18n) | ✅ Terminé |

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
POST /api/v1/pricing/import              # Import prix Partner Center
GET  /api/v1/pricing/products             # Liste produits
GET  /api/v1/pricing/current/{sku}        # Prix actuel
```

#### Analyse & Optimisation
```
POST /api/v1/analyses/                   # Créer analyse
GET  /api/v1/analyses/{id}               # Détails analyse
POST /api/v1/analyses/{id}/recommendations/{id}/accept  # Appliquer reco
```

#### Génération de rapports
```
POST /api/v1/reports/analyses/{id}/pdf    # Rapport PDF
POST /api/v1/reports/analyses/{id}/excel  # Rapport Excel
GET  /api/v1/reports/{id}                 # Télécharger rapport
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
- [LOT11-VALIDATION.md](./LOT11-VALIDATION.md) - Déploiement & Observabilité
- [LOT12-VALIDATION.md](./LOT12-VALIDATION.md) - Internationalisation (i18n)

> [!NOTE]
> Pour les détails sur l'implémentation i18n/l10n, voir [LOT12-VALIDATION.md](./LOT12-VALIDATION.md).

## 🤝 Contribution

1. Créez une branche : `git checkout -b feature/nom`
2. Committez : `git commit -m "Description"`
3. Pushez : `git push origin feature/nom`
4. Ouvrez une Pull Request

## 📄 Licence

Propriétaire - Tous droits réservés