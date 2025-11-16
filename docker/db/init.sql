-- ============================================
-- M365 License Optimizer - Database Initialization
-- Version: 1.0
-- Description: Initial schema setup for development environment
-- ============================================

-- Create main schema
CREATE SCHEMA IF NOT EXISTS optimizer;

-- Set search path
SET search_path TO optimizer, public;

-- ============================================
-- Create Extensions
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization

-- ============================================
-- Create Enums
-- ============================================

-- License status enum
CREATE TYPE license_status AS ENUM ('active', 'suspended', 'disabled', 'trial');

-- Assignment source enum
CREATE TYPE assignment_source AS ENUM ('manual', 'auto', 'group_policy');

-- Offer type enum
CREATE TYPE offer_type AS ENUM ('new_commerce', 'legacy', 'csp');

-- Product family enum
CREATE TYPE product_family AS ENUM ('business', 'enterprise', 'frontline', 'education');

-- Recommendation status enum
CREATE TYPE recommendation_status AS ENUM ('proposed', 'validated', 'rejected', 'sensitive', 'decommission');

-- Analysis status enum
CREATE TYPE analysis_status AS ENUM ('running', 'completed', 'failed', 'cancelled');

-- Trend direction enum
CREATE TYPE trend_direction AS ENUM ('growing', 'stable', 'declining', 'insufficient_data');

-- Onboarding status enum
CREATE TYPE onboarding_status AS ENUM ('pending', 'configured', 'active', 'error');

-- ============================================
-- Create Tables (Basic structure for Lot 1)
-- ============================================

-- Tenant clients table
CREATE TABLE IF NOT EXISTS tenant_clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(36) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL DEFAULT 'FR',
    language VARCHAR(5) NOT NULL DEFAULT 'fr-FR',
    onboarding_status onboarding_status DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tenant app registrations table
CREATE TABLE IF NOT EXISTS tenant_app_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_client_id UUID NOT NULL REFERENCES tenant_clients(id) ON DELETE CASCADE,
    client_id VARCHAR(36) NOT NULL,
    client_secret_encrypted TEXT,
    certificate_thumbprint VARCHAR(255),
    authority_url VARCHAR(500),
    scopes TEXT[] DEFAULT ARRAY[]::TEXT[],
    last_consent_date TIMESTAMP WITH TIME ZONE,
    is_valid BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_client_id, client_id)
);

-- Analysis runs table
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_client_id UUID NOT NULL REFERENCES tenant_clients(id) ON DELETE CASCADE,
    execution_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_seconds NUMERIC(10, 2),
    status analysis_status DEFAULT 'running',
    total_monthly_savings NUMERIC(10, 2),
    total_annual_savings NUMERIC(10, 2),
    cohort_stats JSONB,
    cleanup_stats JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Create Indexes
-- ============================================

-- Tenant clients indexes
CREATE INDEX idx_tenant_clients_tenant_id ON tenant_clients(tenant_id);
CREATE INDEX idx_tenant_clients_status ON tenant_clients(onboarding_status);
CREATE INDEX idx_tenant_clients_country ON tenant_clients(country);

-- Tenant app registrations indexes
CREATE INDEX idx_tenant_app_tenant_client ON tenant_app_registrations(tenant_client_id);
CREATE INDEX idx_tenant_app_valid ON tenant_app_registrations(is_valid);

-- Analyses indexes
CREATE INDEX idx_analyses_tenant_client ON analyses(tenant_client_id);
CREATE INDEX idx_analyses_execution_date ON analyses(execution_date DESC);
CREATE INDEX idx_analyses_status ON analyses(status);

-- ============================================
-- Create Readonly User
-- ============================================

-- Create readonly role for reporting/analytics
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly') THEN
        CREATE ROLE readonly WITH LOGIN PASSWORD 'readonlypass';
    END IF;
END
$$;

-- Grant usage on schema
GRANT USAGE ON SCHEMA optimizer TO readonly;

-- Grant select on all current tables
GRANT SELECT ON ALL TABLES IN SCHEMA optimizer TO readonly;

-- Grant select on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT SELECT ON TABLES TO readonly;

-- Grant usage on sequences (for future needs)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA optimizer TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT USAGE, SELECT ON SEQUENCES TO readonly;

-- ============================================
-- Create Audit/Logging Function (for future GDPR compliance)
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    user_name VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);

-- ============================================
-- Insert Test Data (for development)
-- ============================================

-- Insert sample tenant for testing
INSERT INTO tenant_clients (tenant_id, name, country, language, onboarding_status, metadata)
VALUES 
    ('12345678-1234-1234-1234-123456789012', 'Contoso Ltd', 'FR', 'fr-FR', 'pending', '{"industry": "technology", "size": "medium"}'),
    ('87654321-4321-4321-4321-210987654321', 'Fabrikam Inc', 'US', 'en-US', 'pending', '{"industry": "manufacturing", "size": "large"}')
ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================
-- Database Configuration
-- ============================================

-- Set default privileges for new tables
ALTER DATABASE m365_optimizer SET search_path TO optimizer, public;

-- Enable row-level security (for future multitenant isolation)
-- Will be configured per table in future lots

COMMENT ON SCHEMA optimizer IS 'Main schema for M365 License Optimizer application';
COMMENT ON TABLE tenant_clients IS 'Stores client tenant information for multitenant support';
COMMENT ON TABLE tenant_app_registrations IS 'Stores Azure AD app registration credentials per tenant';
COMMENT ON TABLE analyses IS 'Stores analysis execution history and results';

-- ============================================
-- Completion Message
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'M365 License Optimizer Database Initialized Successfully';
    RAISE NOTICE 'Schema: optimizer';
    RAISE NOTICE 'Tables: tenant_clients, tenant_app_registrations, analyses, audit_logs';
    RAISE NOTICE 'Readonly user: readonly (password: readonlypass)';
    RAISE NOTICE '========================================';
END
$$;
