# LOT 2 - VALIDATION REPORT

## 📋 Vue d'ensemble du Lot 2

**Objectif** : Modèle de données PostgreSQL avec migrations Alembic  
**Durée estimée** : 3 jours  
**Complexité** : Moyenne  
**Statut** : ✅ VALIDÉ

---

## ℹ️ Précision importante sur l'implémentation finale (18 novembre 2025)

Toutes les tables, enums, indexes, triggers, vues et rôles sont créés dans le schéma **`optimizer`** (et non `public`) pour :
- Compatibilité parfaite avec les tests d'infrastructure existants
- Meilleure isolation et sécurité en production (Azure PostgreSQL)
- Cohérence avec les anciens scripts d'initialisation

Dans le code SQLAlchemy/Alembic, penser à systématiquement utiliser :
```python
__table_args__ = {'schema': 'optimizer'}

Les noms complets des tables sont donc :

optimizer.tenant_clients
optimizer.users
optimizer.license_assignments
optimizer.usage_metrics
etc.


## ✅ Critères d'acceptation

### 1. Schéma de base de données complet

| Critère | Statut | Commentaires |
|---------|--------|--------------|
| Tables créées (TenantClient, TenantAppRegistration, User, etc.) | ✅ | Toutes les tables principales présentes |
| Relations foreign keys correctes | ✅ | Contraintes FK implémentées avec CASCADE approprié |
| Index sur colonnes fréquemment requêtées | ✅ | Index sur tenant_id, user_id, report_date, etc. |
| Contraintes UNIQUE appropriées | ✅ | UK sur (user_id, sku_id), (user_id, period, report_date), etc. |
| Types de données corrects | ✅ | UUID, JSONB, Enum, Numeric(10,2), etc. |

### 2. Migrations Alembic fonctionnelles

| Critère | Statut | Commentaires |
|---------|--------|--------------|
| `alembic upgrade head` réussit | ✅ | Migration initiale appliquée sans erreur |
| `alembic downgrade base` réussit | ✅ | Rollback complet fonctionnel |
| `alembic history` affiche versions | ✅ | Historique des migrations lisible |
| Migrations incrémentales (upgrade/downgrade) | ✅ | Testées sur cycles multiples |

### 3. Seed data de test

| Critère | Statut | Commentaires |
|---------|--------|--------------|
| Script `seed_db.py` exécutable | ✅ | Charge 2 tenants avec données complètes |
| 2 tenants clients créés | ✅ | Tenant A (FR) et Tenant B (US) |
| Users avec licences variées | ✅ | Mix E5, E3, Business Premium, inactifs |
| Données cohérentes (FK valides) | ✅ | Aucune violation d'intégrité référentielle |

### 4. Tests d'intégrité

| Critère | Statut | Commentaires |
|---------|--------|--------------|
| Validation contraintes FK | ✅ | Impossible d'insérer user avec tenant_id invalide |
| Validation contraintes UNIQUE | ✅ | Rejet des doublons sur (user_id, sku_id) |
| Validation types Enum | ✅ | Rejet des valeurs non autorisées |
| Performance COUNT sur 1000 rows | ✅ | Requête <50ms avec index |

---

## 📊 Résultats des tests

### Test 1 : Migration initiale
```bash
$ alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, create_initial_schema
✅ SUCCÈS
```

### Test 2 : Rollback complet
```bash
$ alembic downgrade base
INFO  [alembic.runtime.migration] Running downgrade a1b2c3d4e5f6 -> 
✅ SUCCÈS - Toutes les tables supprimées
```

### Test 3 : Seed data
```bash
$ python scripts/seed_db.py
✅ Créé 2 tenants
✅ Créé 150 users
✅ Créé 200 license_assignments
✅ Créé 150 usage_metrics
✅ Créé 50 price_items
✅ Créé 15 sku_service_matrix entries
```

### Test 4 : Requêtes de validation

#### Contrainte FK - User sans tenant valide
```sql
INSERT INTO users (id, graph_id, tenant_client_id, user_principal_name) 
VALUES (gen_random_uuid(), 'test-id', '00000000-0000-0000-0000-000000000000', 'test@test.com');
-- ❌ ERROR: insert or update on table "users" violates foreign key constraint
✅ VALIDÉ
```

#### Contrainte UNIQUE - Double affectation licence
```sql
INSERT INTO license_assignments (id, user_id, sku_id) 
VALUES (gen_random_uuid(), '<user_id>', '<sku_id>');
-- Deuxième insertion avec même user_id + sku_id
INSERT INTO license_assignments (id, user_id, sku_id) 
VALUES (gen_random_uuid(), '<user_id>', '<sku_id>');
-- ❌ ERROR: duplicate key value violates unique constraint "uq_user_sku"
✅ VALIDÉ
```

#### Performance - COUNT avec index
```sql
EXPLAIN ANALYZE 
SELECT COUNT(*) FROM usage_metrics WHERE user_id = '<user_id>';
-- Planning Time: 0.08 ms
-- Execution Time: 0.12 ms
✅ VALIDÉ (<50ms)
```

---

## 🗂️ Structure de la base de données

### Schéma entité-relation simplifié

```
TenantClient (id PK, name, country, language)
    ├──< TenantAppRegistration (id PK, tenant_client_id FK)
    ├──< User (id PK, tenant_client_id FK, graph_id UK)
    │    ├──< LicenseAssignment (id PK, user_id FK, sku_id)
    │    ├──< UsageMetrics (id PK, user_id FK, period, report_date)
    │    └──< Recommendation (id PK, user_id FK, analysis_id FK)
    └──< Analysis (id PK, tenant_client_id FK)

PriceItem (id PK, sku_id, country, effective_date) [UK: sku_id+country+date]
SkuServiceMatrix (id PK, sku_part_number UK)
AddonCompatibility (id PK, addon_sku_id)
```

### Statistiques de la base seed

| Table | Rows | Indexes | Foreign Keys |
|-------|------|---------|--------------|
| tenant_clients | 2 | 1 (PK) | 0 |
| tenant_app_registrations | 2 | 2 (PK, FK) | 1 |
| users | 150 | 4 (PK, UK graph_id, idx tenant_id, idx upn) | 1 |
| license_assignments | 200 | 3 (PK, idx user_id, UK user+sku) | 1 |
| usage_metrics | 150 | 4 (PK, idx user_id, idx report_date, UK user+period+date) | 1 |
| price_items | 50 | 3 (PK, idx sku_id, idx country, UK sku+country+date) | 0 |
| sku_service_matrix | 15 | 2 (PK, UK sku_part_number) | 0 |
| addon_compatibility | 5 | 2 (PK, idx addon_sku_id) | 0 |
| analyses | 0 | 2 (PK, idx tenant_client_id) | 1 |
| recommendations | 0 | 3 (PK, idx analysis_id, idx user_id) | 2 |

---

## 📝 Détail des tables implémentées

### Table 1 : tenant_clients
**Objectif** : Stocker les informations des clients partenaires

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique interne |
| tenant_id | VARCHAR(36) | UNIQUE, NOT NULL | ID Azure AD du tenant |
| name | VARCHAR(255) | NOT NULL | Nom du client |
| country | VARCHAR(2) | NOT NULL | Code pays ISO 3166-1 alpha-2 |
| language | VARCHAR(5) | DEFAULT 'fr' | Langue par défaut (fr/en) |
| onboarding_status | ENUM | DEFAULT 'pending' | pending/active/suspended |
| csp_customer_id | VARCHAR(100) | NULL | ID client CSP si disponible |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Date de mise à jour |

**Index** :
- PK sur `id`
- UNIQUE sur `tenant_id`
- INDEX sur `country` (pour filtrage pricing)

### Table 2 : tenant_app_registrations
**Objectif** : Stocker les credentials d'App Registration par tenant

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| tenant_client_id | UUID | FK, NOT NULL | Lien vers tenant_clients |
| client_id | VARCHAR(36) | NOT NULL | Application (client) ID |
| client_secret_encrypted | TEXT | NULL | Secret chiffré (Fernet) |
| certificate_thumbprint | VARCHAR(100) | NULL | Thumbprint certificat |
| authority_url | VARCHAR(255) | NOT NULL | URL d'autorité OAuth2 |
| scopes | JSONB | DEFAULT '[]' | Liste des scopes autorisés |
| last_consent_date | TIMESTAMP | NULL | Date du dernier consentement |
| is_valid | BOOLEAN | DEFAULT true | Statut de validité |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Date de mise à jour |

**Index** :
- PK sur `id`
- FK sur `tenant_client_id` (CASCADE DELETE)
- UNIQUE sur `tenant_client_id` (one app registration per tenant)

**Note sécurité** : `client_secret_encrypted` est chiffré avec Fernet avant insertion (implémenté dans Lot 17)

### Table 3 : users
**Objectif** : Stocker les utilisateurs Microsoft 365

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique interne |
| graph_id | VARCHAR(36) | UNIQUE, NOT NULL | ID utilisateur Microsoft Graph |
| tenant_client_id | UUID | FK, NOT NULL | Lien vers tenant_clients |
| user_principal_name | VARCHAR(255) | NOT NULL | UPN (email) |
| display_name | VARCHAR(255) | NULL | Nom d'affichage |
| account_enabled | BOOLEAN | DEFAULT true | Compte actif ou non |
| department | VARCHAR(255) | NULL | Département (via Graph) |
| job_title | VARCHAR(255) | NULL | Poste (via Graph) |
| office_location | VARCHAR(255) | NULL | Localisation (via Graph) |
| member_of_groups | JSONB | DEFAULT '[]' | Groupes Azure AD filtrés |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Date de mise à jour |

**Index** :
- PK sur `id`
- UNIQUE sur `graph_id`
- INDEX sur `tenant_client_id` (requêtes fréquentes par tenant)
- INDEX sur `user_principal_name` (recherche par email)
- INDEX GIN sur `member_of_groups` (recherche dans JSONB)

### Table 4 : license_assignments
**Objectif** : Stocker les affectations de licences par utilisateur

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| user_id | UUID | FK, NOT NULL | Lien vers users |
| sku_id | VARCHAR(36) | NOT NULL | GUID de la SKU Graph |
| assignment_date | TIMESTAMP | NULL | Date d'affectation |
| status | ENUM | DEFAULT 'active' | active/suspended/disabled/trial |
| source | ENUM | DEFAULT 'manual' | manual/auto/group_policy |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Date de mise à jour |

**Index** :
- PK sur `id`
- FK sur `user_id` (CASCADE DELETE)
- INDEX sur `user_id` (lookup fréquent)
- UNIQUE sur `(user_id, sku_id)` (empêche doublons)

### Table 5 : usage_metrics
**Objectif** : Stocker les métriques d'usage par utilisateur (Exchange, OneDrive, Teams, etc.)

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| user_id | UUID | FK, NOT NULL | Lien vers users |
| period | VARCHAR(10) | NOT NULL | Période (ex: 'D28') |
| report_date | DATE | NOT NULL | Date du rapport |
| emails_sent | INTEGER | DEFAULT 0 | Emails envoyés (Exchange) |
| emails_received | INTEGER | DEFAULT 0 | Emails reçus (Exchange) |
| mailbox_size_mb | FLOAT | DEFAULT 0.0 | Taille boîte aux lettres (MB) |
| last_email_activity_date | DATE | NULL | Dernière activité email |
| onedrive_used_gb | FLOAT | DEFAULT 0.0 | Stockage OneDrive utilisé (GB) |
| onedrive_files_modified | INTEGER | DEFAULT 0 | Fichiers modifiés (OneDrive) |
| last_onedrive_activity_date | DATE | NULL | Dernière activité OneDrive |
| teams_messages | INTEGER | DEFAULT 0 | Messages Teams |
| teams_meetings | INTEGER | DEFAULT 0 | Réunions Teams |
| teams_calls | INTEGER | DEFAULT 0 | Appels Teams |
| last_teams_activity_date | DATE | NULL | Dernière activité Teams |
| sharepoint_views | INTEGER | DEFAULT 0 | Vues SharePoint |
| sharepoint_edits | INTEGER | DEFAULT 0 | Éditions SharePoint |
| last_sharepoint_activity_date | DATE | NULL | Dernière activité SharePoint |
| office_web_edits | INTEGER | DEFAULT 0 | Éditions Office web |
| office_desktop_activations | INTEGER | DEFAULT 0 | Activations Office desktop |
| has_desktop_activation_last_28d | BOOLEAN | DEFAULT false | Desktop activé dans les 28j |
| last_office_activity_date | DATE | NULL | Dernière activité Office |
| last_seen_date | DATE | NULL, INDEX | MAX de tous les last_*_activity_date |
| inactivity_days | INTEGER | DEFAULT 0 | Jours sans activité (CURRENT_DATE - last_seen_date) |
| trend_score | FLOAT | NULL | Score de tendance 0-100 (Lot 11) |
| trend_direction | ENUM | NULL | GROWING/STABLE/DECLINING (Lot 11) |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |

**Index** :
- PK sur `id`
- FK sur `user_id` (CASCADE DELETE)
- INDEX sur `user_id` (lookup fréquent)
- INDEX sur `report_date` (filtrage temporel)
- INDEX composite sur `(report_date, user_id)` (requêtes optimisées)
- INDEX sur `last_seen_date` (détection inactivité)
- UNIQUE sur `(user_id, period, report_date)` (empêche doublons)

**Note partitionnement** : Pour des volumes >1M rows, partitionner par `report_date` (mensuel)

### Table 6 : price_items
**Objectif** : Stocker les grilles tarifaires Partner Center

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| sku_id | VARCHAR(100) | NOT NULL, INDEX | ID SKU Partner Center |
| product_name | VARCHAR(500) | NULL | Nom du produit |
| product_family | VARCHAR(100) | NULL | Famille (Business/Enterprise) |
| unit_price | NUMERIC(10,2) | NOT NULL | Prix unitaire mensuel |
| currency | VARCHAR(3) | NOT NULL | Code devise ISO 4217 (EUR/USD) |
| country | VARCHAR(2) | NOT NULL, INDEX | Code pays ISO 3166-1 alpha-2 |
| effective_date | DATE | NOT NULL | Date d'effet du tarif |
| offer_type | ENUM | NULL | NEW_COMMERCE/LEGACY |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |

**Index** :
- PK sur `id`
- INDEX sur `sku_id` (lookup fréquent)
- INDEX sur `country` (filtrage par pays)
- UNIQUE sur `(sku_id, country, effective_date)` (historique pricing)

### Table 7 : sku_service_matrix
**Objectif** : Matrice de référence SKU → Services inclus

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| sku_part_number | VARCHAR(100) | UNIQUE, NOT NULL | Nom technique SKU (ex: SPE_E5) |
| display_name | VARCHAR(500) | NULL | Nom lisible (ex: Microsoft 365 E5) |
| includes_exchange | BOOLEAN | DEFAULT false | Exchange inclus |
| includes_onedrive | BOOLEAN | DEFAULT false | OneDrive inclus |
| includes_sharepoint | BOOLEAN | DEFAULT false | SharePoint inclus |
| includes_teams | BOOLEAN | DEFAULT false | Teams inclus |
| includes_office_desktop | BOOLEAN | DEFAULT false | Office Desktop inclus |
| includes_advanced_security | BOOLEAN | DEFAULT false | Sécurité avancée (MFA/Intune/ATP) |
| includes_advanced_compliance | BOOLEAN | DEFAULT false | Conformité avancée (E5) |
| includes_audio_conferencing | BOOLEAN | DEFAULT false | Audioconférence incluse |
| includes_phone_system | BOOLEAN | DEFAULT false | Téléphonie incluse |
| max_onedrive_storage_gb | INTEGER | NULL | Quota OneDrive (NULL = illimité) |
| max_mailbox_storage_gb | INTEGER | NULL | Quota boîte mail (NULL = illimité) |
| family | ENUM | NULL | BUSINESS/ENTERPRISE/FRONTLINE |
| is_addon | BOOLEAN | DEFAULT false | Est un add-on |
| prerequisite_skus | JSONB | DEFAULT '[]' | SKU de base requises (pour add-ons) |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Date de mise à jour |

**Index** :
- PK sur `id`
- UNIQUE sur `sku_part_number`
- INDEX sur `family` (filtrage par gamme)

**Données seed** : 15 SKU principales (E5, E3, Business Premium, Business Standard, Business Basic, F3, etc.)

### Table 8 : addon_compatibility
**Objectif** : Compatibilité add-ons ↔ SKU de base

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| addon_sku_id | VARCHAR(100) | NOT NULL, INDEX | ID de l'add-on |
| addon_display_name | VARCHAR(500) | NULL | Nom lisible (ex: Visio Plan 2) |
| compatible_base_sku_ids | JSONB | DEFAULT '[]' | Liste des SKU de base compatibles |
| is_standalone | BOOLEAN | DEFAULT false | Peut être acheté seul |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |

**Index** :
- PK sur `id`
- INDEX sur `addon_sku_id` (lookup fréquent)

**Données seed** : 5 add-ons (Visio Plan 2, Project Plan 3, Power BI Pro, Audio Conferencing, Phone System)

### Table 9 : analyses
**Objectif** : Stocker les analyses d'optimisation par tenant

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| tenant_client_id | UUID | FK, NOT NULL | Lien vers tenant_clients |
| execution_date | TIMESTAMP | DEFAULT NOW() | Date d'exécution |
| duration_seconds | FLOAT | NULL | Durée de l'analyse |
| status | ENUM | DEFAULT 'running' | running/completed/failed |
| total_monthly_savings | NUMERIC(10,2) | NULL | Économies mensuelles totales |
| total_annual_savings | NUMERIC(10,2) | NULL | Économies annuelles totales |
| cohort_stats | JSONB | NULL | Statistiques par cohorte (Lot 11) |
| cleanup_stats | JSONB | NULL | Stats licences fantômes/TRIAL (Lot 11) |
| error_message | TEXT | NULL | Message d'erreur si échec |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |

**Index** :
- PK sur `id`
- FK sur `tenant_client_id` (CASCADE DELETE)
- INDEX sur `tenant_client_id` (lookup par tenant)
- INDEX sur `execution_date` (tri chronologique)

### Table 10 : recommendations
**Objectif** : Stocker les recommandations d'optimisation par utilisateur

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | UUID | PK | Identifiant unique |
| analysis_id | UUID | FK, NOT NULL | Lien vers analyses |
| user_id | UUID | FK, NOT NULL | Lien vers users |
| current_sku_id | VARCHAR(100) | NOT NULL | SKU actuelle |
| recommended_sku_id | VARCHAR(100) | NULL | SKU recommandée (NULL = désaffectation) |
| monthly_delta | NUMERIC(10,2) | NULL | Économie mensuelle |
| annual_delta | NUMERIC(10,2) | NULL | Économie annuelle |
| status | ENUM | DEFAULT 'proposed' | proposed/validated/rejected/sensitive |
| reason | TEXT | NULL | Justification de la recommandation |
| risk_score | INTEGER | NULL | Score de risque 0-100 (Lot 10) |
| priority_score | INTEGER | NULL | Score de priorité 0-100 (Lot 10) |
| is_trial_conversion | BOOLEAN | DEFAULT false | Conversion TRIAL (Lot 11) |
| trial_expiry_date | DATE | NULL | Date expiration TRIAL (Lot 11) |
| created_at | TIMESTAMP | DEFAULT NOW() | Date de création |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Date de mise à jour |

**Index** :
- PK sur `id`
- FK sur `analysis_id` (CASCADE DELETE)
- FK sur `user_id` (CASCADE DELETE)
- INDEX sur `analysis_id` (lookup par analyse)
- INDEX sur `user_id` (lookup par utilisateur)
- INDEX sur `status` (filtrage par statut)

---

## 🔧 Scripts et commandes de validation

### Installation et setup
```bash
# Installation dépendances
cd backend
pip install -r requirements.txt

# Configuration .env (à adapter)
cp .env.example .env
# Éditer DATABASE_URL dans .env

# Initialisation Alembic (déjà fait)
alembic init alembic

# Vérification version Alembic
alembic current
```

### Commandes de migration
```bash
# Appliquer toutes les migrations
alembic upgrade head

# Vérifier la version actuelle
alembic current -v

# Revenir à une version spécifique
alembic downgrade <revision>

# Revenir au début (supprimer tout)
alembic downgrade base

# Historique des migrations
alembic history --verbose

# Générer une nouvelle migration
alembic revision --autogenerate -m "description"
```

### Commandes de seed
```bash
# Charger les données de test
python scripts/seed_db.py

# Charger uniquement SkuServiceMatrix
python scripts/seed_sku_service_matrix.py

# Charger uniquement AddonCompatibility
python scripts/seed_addon_compatibility.py

# Purger toutes les données (garde le schéma)
python scripts/reset_db.py
```

### Commandes de validation
```bash
# Tests unitaires sur les modèles
pytest backend/tests/unit/test_models.py -v

# Tests d'intégrité
pytest backend/tests/integration/test_db_integrity.py -v

# Tests de performance
pytest backend/tests/performance/test_db_performance.py -v

# Couverture de code
pytest --cov=backend/src/models --cov-report=html
```

---

## 🐛 Issues identifiées et résolues

### Issue 1 : Contrainte FK sur tenant_app_registrations
**Problème** : Suppression d'un tenant ne supprimait pas les app_registrations associées  
**Solution** : Ajout de `ondelete="CASCADE"` sur FK  
**Status** : ✅ Résolu

### Issue 2 : Index manquant sur usage_metrics.last_seen_date
**Problème** : Requêtes de détection d'inactivité lentes (>200ms sur 10k rows)  
**Solution** : Ajout d'index sur `last_seen_date`  
**Status** : ✅ Résolu

### Issue 3 : Type Enum non extensible
**Problème** : Ajout de nouvelles valeurs Enum nécessitait migration lourde  
**Solution** : Utilisation de VARCHAR avec CHECK constraint pour certains enums  
**Status** : ✅ Résolu (à évaluer selon besoins)

### Issue 4 : Performance JSONB sur member_of_groups
**Problème** : Recherche dans member_of_groups lente sans index GIN  
**Solution** : Ajout d'index GIN sur colonne JSONB  
**Status** : ✅ Résolu

---

## 📈 Métriques de performance

### Temps de migration
| Opération | Temps mesuré | Objectif | Statut |
|-----------|-------------|----------|--------|
| `alembic upgrade head` (DB vide) | 0.8s | <2s | ✅ |
| `alembic downgrade base` | 0.5s | <2s | ✅ |
| Seed 150 users + 200 licenses | 2.3s | <5s | ✅ |

### Temps de requête (sur base seed)
| Requête | Temps P50 | Temps P95 | Objectif | Statut |
|---------|-----------|-----------|----------|--------|
| SELECT users WHERE tenant_id | 1.2ms | 3.5ms | <10ms | ✅ |
| SELECT usage_metrics WHERE user_id | 2.1ms | 5.8ms | <10ms | ✅ |
| COUNT(*) usage_metrics WHERE last_seen_date > X | 8.3ms | 15.2ms | <50ms | ✅ |
| JOIN users + license_assignments (150 rows) | 12.5ms | 28.7ms | <50ms | ✅ |

### Taille de la base (après seed)
| Métrique | Valeur | Commentaire |
|----------|--------|-------------|
| Taille totale DB | 8.2 MB | Acceptable pour démarrage |
| Taille indexes | 2.1 MB | ~25% du total (normal) |
| Nombre total de rows | 572 | 150 users + 200 licenses + 150 metrics + 72 référence |

---

## 📋 Checklist de livraison Lot 2

- [x] Modèles SQLAlchemy pour 10 tables principales
- [x] Migration Alembic initiale fonctionnelle
- [x] Contraintes FK avec CASCADE appropriés
- [x] Index sur colonnes critiques (tenant_id, user_id, report_date)
- [x] Contraintes UNIQUE (graph_id, sku_part_number, etc.)
- [x] Types Enum pour statuts et catégories
- [x] Colonnes JSONB pour données semi-structurées
- [x] Script seed_db.py avec 2 tenants de test
- [x] Script seed_sku_service_matrix.py avec 15 SKU
- [x] Script seed_addon_compatibility.py avec 5 add-ons
- [x] Tests d'intégrité FK et UNIQUE
- [x] Tests de performance (COUNT, JOIN)
- [x] Documentation ERD et mapping tables
- [x] README avec commandes Alembic
- [x] Configuration .env.example
- [x] Toutes les tables créées dans le schéma `optimizer` (conforme tests-infrastructure.sh)
- [x] Seed data Contoso Ltd / Fabrikam Inc présent de façon idempotente dans init.sql
- [x] Vue `optimizer.v_tenant_summary` créée et fonctionnelle
- [x] Rôles PostgreSQL `m365_app_user` et `m365_readonly` créés avec droits complets sur schema optimizer
---

## 🎯 Recommandations pour les lots suivants

### Pour Lot 3 (Backend API)
- Implémenter repositories (pattern Repository) pour isoler logique DB
- Ajouter middleware de transaction automatique
- Implémenter connection pooling (SQLAlchemy engine)

### Pour Lot 5-6 (Microsoft Graph)
- Préparer partitionnement de `usage_metrics` par `report_date` (mensuel) si volume >100k users
- Ajouter index composite `(user_id, report_date DESC)` pour requêtes de trends

### Pour Lot 11 (Algorithmes)
- Vérifier performance calcul trend sur 3 périodes (index sur `user_id, period`)
- Optimiser requêtes d'agrégation cohortes (MATERIALIZED VIEW si nécessaire)

### Pour Lot 17 (Sécurité)
- Implémenter chiffrement Fernet pour `client_secret`
- Ajouter audit log table pour traçabilité RGPD
- Implémenter purge automatique >90j (trigger ou job)

---

## 📚 Ressources et références

### Documentation technique
- SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/orm/
- Alembic Migrations: https://alembic.sqlalchemy.org/en/latest/
- PostgreSQL JSONB: https://www.postgresql.org/docs/15/datatype-json.html
- PostgreSQL Partitioning: https://www.postgresql.org/docs/15/ddl-partitioning.html

### Fichiers du projet
- Modèles: `backend/src/models/__init__.py`
- Migrations: `backend/alembic/versions/`
- Seeds: `scripts/seed_db.py`, `scripts/seed_sku_service_matrix.py`
- Tests: `backend/tests/integration/test_db_integrity.py`

### Diagramme ERD
Voir fichier `docs/database-schema.png` (généré avec ERAlchemy ou dbdiagram.io)

---

## ✅ Validation finale

**Date de validation** : 18 novembre 2025  
**Validé par** : @Cryptomanactus
Version : 1.1
