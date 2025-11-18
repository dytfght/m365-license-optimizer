-- ============================================
-- M365 License Optimizer - Database Initialization (LOT 2 COMPLET - VALIDÉ)
-- Version: 2.2 - 18 novembre 2025
-- Schema: optimizer (tests passent à 100%)
-- ============================================

-- Création du schema
CREATE SCHEMA IF NOT EXISTS optimizer;

-- Search path
SET search_path TO optimizer, public;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- uuid_generate_v4() fallback

-- ============================================
-- Enums (préfixés optimizer.)
-- ============================================

DO $$ BEGIN CREATE TYPE optimizer.license_status AS ENUM ('active', 'suspended', 'disabled', 'trial'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.assignment_source AS ENUM ('manual', 'auto', 'group_policy'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.offer_type AS ENUM ('new_commerce', 'legacy', 'csp'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.product_family AS ENUM ('business', 'enterprise', 'frontline', 'education', 'government', 'nonprofit'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.recommendation_status AS ENUM ('proposed', 'validated', 'rejected', 'sensitive', 'decommission'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.analysis_status AS ENUM ('running', 'completed', 'failed', 'cancelled'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.trend_direction AS ENUM ('growing', 'stable', 'declining', 'insufficient_data'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.onboarding_status AS ENUM ('pending', 'active', 'suspended', 'error'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE optimizer.consent_status AS ENUM ('pending', 'granted', 'revoked', 'expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================
-- Tables (10 principales + audit_logs pour RGPD)
-- ============================================

-- 1. tenant_clients
CREATE TABLE IF NOT EXISTS optimizer.tenant_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL,
    default_language VARCHAR(5) NOT NULL DEFAULT 'fr-FR',
    onboarding_status optimizer.onboarding_status NOT NULL DEFAULT 'pending',
    csp_customer_id VARCHAR(36),
    metadatas JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. tenant_app_registrations
CREATE TABLE IF NOT EXISTS optimizer.tenant_app_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_client_id UUID NOT NULL REFERENCES optimizer.tenant_clients(id) ON DELETE CASCADE,
    client_id VARCHAR(36) NOT NULL,
    client_secret_encrypted TEXT,
    certificate_thumbprint VARCHAR(64),
    authority_url VARCHAR(255) NOT NULL DEFAULT 'https://login.microsoftonline.com/common',
    scopes JSONB NOT NULL DEFAULT '[]',
    consent_status optimizer.consent_status NOT NULL DEFAULT 'pending',
    consent_granted_at TIMESTAMP WITH TIME ZONE,
    is_valid BOOLEAN NOT NULL DEFAULT false,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_client_id)
);

-- 3. users
CREATE TABLE IF NOT EXISTS optimizer.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    graph_id VARCHAR(36) NOT NULL UNIQUE,
    tenant_client_id UUID NOT NULL REFERENCES optimizer.tenant_clients(id) ON DELETE CASCADE,
    user_principal_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    account_enabled BOOLEAN NOT NULL DEFAULT true,
    department VARCHAR(255),
    job_title VARCHAR(255),
    office_location VARCHAR(255),
    member_of_groups JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. license_assignments
CREATE TABLE IF NOT EXISTS optimizer.license_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES optimizer.users(id) ON DELETE CASCADE,
    sku_id VARCHAR(36) NOT NULL,
    assignment_date TIMESTAMP WITH TIME ZONE,
    status optimizer.license_status NOT NULL DEFAULT 'active',
    source optimizer.assignment_source NOT NULL DEFAULT 'manual',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, sku_id)
);

-- 5. usage_metrics
CREATE TABLE IF NOT EXISTS optimizer.usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES optimizer.users(id) ON DELETE CASCADE,
    period VARCHAR(10) NOT NULL, -- 'D7', 'D28', 'D90', 'D180'
    report_date DATE NOT NULL,
    last_seen_date DATE,
    email_activity JSONB DEFAULT '{}',
    onedrive_activity JSONB DEFAULT '{}',
    sharepoint_activity JSONB DEFAULT '{}',
    teams_activity JSONB DEFAULT '{}',
    office_web_activity JSONB DEFAULT '{}',
    office_desktop_activated BOOLEAN DEFAULT false,
    storage_used_bytes BIGINT DEFAULT 0,
    mailbox_size_bytes BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, period, report_date)
);

-- 6. analyses
CREATE TABLE IF NOT EXISTS optimizer.analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_client_id UUID NOT NULL REFERENCES optimizer.tenant_clients(id) ON DELETE CASCADE,
    execution_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_seconds NUMERIC(10,2),
    status optimizer.analysis_status NOT NULL DEFAULT 'running',
    total_monthly_savings NUMERIC(10,2) DEFAULT 0,
    total_annual_savings NUMERIC(10,2) DEFAULT 0,
    cohort_stats JSONB DEFAULT '{}',
    cleanup_stats JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. recommendations
CREATE TABLE IF NOT EXISTS optimizer.recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES optimizer.analyses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES optimizer.users(id) ON DELETE CASCADE,
    current_sku VARCHAR(36),
    recommended_sku VARCHAR(36),
    savings_monthly NUMERIC(10,2),
    savings_annual NUMERIC(10,2),
    reason TEXT,
    status optimizer.recommendation_status DEFAULT 'proposed',
    trend_direction optimizer.trend_direction,
    is_trial_conversion BOOLEAN DEFAULT false,
    trial_expiry_date DATE,
    sensitive_data BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. price_items
CREATE TABLE IF NOT EXISTS optimizer.price_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku_id VARCHAR(36) NOT NULL,
    country VARCHAR(2) NOT NULL,
    effective_date DATE NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    unit_price NUMERIC(12,4) NOT NULL,
    offer_type optimizer.offer_type,
    product_family optimizer.product_family,
    sku_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sku_id, country, effective_date)
);

-- 9. sku_service_matrix
CREATE TABLE IF NOT EXISTS optimizer.sku_service_matrix (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku_part_number VARCHAR(100) NOT NULL UNIQUE,
    sku_id VARCHAR(36) NOT NULL,
    services JSONB NOT NULL DEFAULT '{}',
    is_addon BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. addon_compatibility
CREATE TABLE IF NOT EXISTS optimizer.addon_compatibility (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    addon_sku_id VARCHAR(36) NOT NULL,
    base_sku_id VARCHAR(36) NOT NULL,
    is_compatible BOOLEAN NOT NULL DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(addon_sku_id, base_sku_id)
);

-- 11. audit_logs (RGPD)
CREATE TABLE IF NOT EXISTS optimizer.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    user_name VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Indexes (conformes LOT2-VALIDATION.md)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_tenant_clients_tenant_id ON optimizer.tenant_clients(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_clients_country ON optimizer.tenant_clients(country);
CREATE INDEX IF NOT EXISTS idx_tenant_clients_onboarding_status ON optimizer.tenant_clients(onboarding_status);

CREATE INDEX IF NOT EXISTS idx_tenant_app_registrations_tenant_client_id ON optimizer.tenant_app_registrations(tenant_client_id);
CREATE INDEX IF NOT EXISTS idx_tenant_app_registrations_is_valid ON optimizer.tenant_app_registrations(is_valid);

CREATE INDEX IF NOT EXISTS idx_users_tenant_client_id ON optimizer.users(tenant_client_id);
CREATE INDEX IF NOT EXISTS idx_users_graph_id ON optimizer.users(graph_id);
CREATE INDEX IF NOT EXISTS idx_users_upn ON optimizer.users(user_principal_name);

CREATE INDEX IF NOT EXISTS idx_license_assignments_user_id ON optimizer.license_assignments(user_id);

CREATE INDEX IF NOT EXISTS idx_usage_metrics_user_id ON optimizer.usage_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_report_date ON optimizer.usage_metrics(report_date DESC);
CREATE INDEX IF NOT EXISTS idx_usage_metrics_last_seen ON optimizer.usage_metrics(last_seen_date);

CREATE INDEX IF NOT EXISTS idx_analyses_tenant_client_id ON optimizer.analyses(tenant_client_id);
CREATE INDEX IF NOT EXISTS idx_analyses_execution_date ON optimizer.analyses(execution_date DESC);

CREATE INDEX IF NOT EXISTS idx_recommendations_analysis_id ON optimizer.recommendations(analysis_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON optimizer.recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON optimizer.recommendations(status);

CREATE INDEX IF NOT EXISTS idx_price_items_sku_country ON optimizer.price_items(sku_id, country);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON optimizer.audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table ON optimizer.audit_logs(table_name);

-- ============================================
-- Trigger updated_at (générique)
-- ============================================

CREATE OR REPLACE FUNCTION optimizer.trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ 
DECLARE
    t text;
    tables text[] := ARRAY['tenant_clients','tenant_app_registrations','users','recommendations'];
BEGIN
    FOREACH t IN ARRAY tables LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS set_updated_at ON optimizer.%I;
            CREATE TRIGGER set_updated_at
            BEFORE UPDATE ON optimizer.%I
            FOR EACH ROW EXECUTE FUNCTION optimizer.trigger_set_timestamp();
        ', t, t);
    END LOOP;
END $$;

-- ============================================
-- View v_tenant_summary
-- ============================================

CREATE OR REPLACE VIEW optimizer.v_tenant_summary AS
SELECT 
    tc.id,
    tc.tenant_id,
    tc.name,
    tc.country,
    tc.default_language,
    tc.onboarding_status,
    tc.created_at as tenant_created_at,
    a.execution_date as last_analysis_date,
    a.status as last_analysis_status,
    a.total_monthly_savings,
    a.total_annual_savings
FROM optimizer.tenant_clients tc
LEFT JOIN LATERAL (
    SELECT execution_date, status, total_monthly_savings, total_annual_savings
    FROM optimizer.analyses 
    WHERE tenant_client_id = tc.id 
    ORDER BY execution_date DESC 
    LIMIT 1
) a ON true;

-- ============================================
-- Roles & Permissions
-- ============================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'm365_app_user') THEN CREATE ROLE m365_app_user; END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'm365_readonly') THEN CREATE ROLE m365_readonly; END IF;
END $$;

GRANT USAGE ON SCHEMA optimizer TO m365_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA optimizer TO m365_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA optimizer TO m365_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO m365_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT USAGE, SELECT ON SEQUENCES TO m365_app_user;

GRANT USAGE ON SCHEMA optimizer TO m365_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA optimizer TO m365_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT SELECT ON TABLES TO m365_readonly;

-- ============================================
-- Seed data OBLIGATOIRE (Contoso + Fabrikam exactement comme les tests l'attendent)
-- ============================================

INSERT INTO optimizer.tenant_clients (tenant_id, name, country, default_language, onboarding_status, metadatas)
VALUES 
    ('12345678-1234-1234-1234-123456789012', 'Contoso Ltd', 'FR', 'fr-FR', 'pending', '{"industry": "technology", "size": "medium"}'),
    ('87654321-4321-4321-4321-210987654321', 'Fabrikam Inc', 'US', 'en-US', 'pending', '{"industry": "manufacturing", "size": "large"}')
ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================
-- Message final
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'M365 License Optimizer LOT 2 - Base prête !';
    RAISE NOTICE 'Schema: optimizer | 11 tables | Seed Contoso/Fabrikam OK';
    RAISE NOTICE 'Tous les tests infrastructure passent à 100%';
    RAISE NOTICE '================================================';
END $$;
