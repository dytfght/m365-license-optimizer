-- ============================================
-- M365 License Optimizer - Database Bootstrap
-- Version: 3.0 - LOT4 - Alembic-first approach
-- ============================================
-- Ce fichier ne crée QUE :
-- 1. Le schéma optimizer (Alembic suppose qu'il existe)
-- 2. Les rôles et permissions (non gérés par Alembic)
-- 3. Les extensions nécessaires (aucune pour ce projet)
-- 
-- TOUTES les tables sont créées par Alembic migrations
-- Ce fichier est COMPLÉMENTAIRE à Alembic, pas redondant
-- ============================================

-- Extensions (PostgreSQL 13+ a gen_random_uuid() natif)
-- Aucune extension nécessaire pour ce projet

-- ============================================
-- Création du schéma optimizer
-- ============================================
CREATE SCHEMA IF NOT EXISTS optimizer;

-- Search path par défaut
ALTER DATABASE m365_optimizer SET search_path TO optimizer, public;

-- ============================================
-- Rôles et permissions
-- ============================================

-- Rôle applicatif (backend FastAPI)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'm365_app_user') THEN
        CREATE ROLE m365_app_user LOGIN PASSWORD 'CHANGE_IN_PRODUCTION';
    END IF;
END $$;

-- Rôle lecture seule (reporting, analytics)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'm365_readonly') THEN
        CREATE ROLE m365_readonly LOGIN PASSWORD 'CHANGE_IN_PRODUCTION';
    END IF;
END $$;

-- Permissions sur le schéma optimizer
GRANT USAGE ON SCHEMA optimizer TO m365_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA optimizer TO m365_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA optimizer TO m365_app_user;

-- Permissions par défaut pour les futurs objets
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer 
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO m365_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer 
    GRANT USAGE, SELECT ON SEQUENCES TO m365_app_user;

-- Permissions lecture seule
GRANT USAGE ON SCHEMA optimizer TO m365_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA optimizer TO m365_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer 
    GRANT SELECT ON TABLES TO m365_readonly;

-- ============================================
-- Message de confirmation
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'M365 License Optimizer - Database Bootstrap OK';
    RAISE NOTICE 'Schema: optimizer created';
    RAISE NOTICE 'Roles: m365_app_user, m365_readonly created';
    RAISE NOTICE 'Next: Run "alembic upgrade head" to create tables';
    RAISE NOTICE '================================================';
END $$;
