-- ============================================
-- M365 License Optimizer - Database Initialization
-- Version: 1.0 - Azure PostgreSQL Flexible Server Compatible
-- Description: Initial schema setup for development environment
-- ============================================

-- Create main schema
CREATE SCHEMA IF NOT EXISTS optimizer;

-- Set search path
SET search_path TO optimizer, public;

-- ============================================
-- Create Extensions (Azure Flexible Server compatible)
-- ============================================

-- Enable pgcrypto extension for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- Create Enums
-- ============================================

-- License status enum
DO $$ BEGIN
    CREATE TYPE optimizer.license_status AS ENUM ('active', 'suspended', 'disabled', 'trial');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Assignment source enum
DO $$ BEGIN
    CREATE TYPE optimizer.assignment_source AS ENUM ('manual', 'auto', 'group_policy');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Offer type enum
DO $$ BEGIN
    CREATE TYPE optimizer.offer_type AS ENUM ('new_commerce', 'legacy', 'csp');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Product family enum
DO $$ BEGIN
    CREATE TYPE optimizer.product_family AS ENUM ('business', 'enterprise', 'frontline', 'education');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Recommendation status enum
DO $$ BEGIN
    CREATE TYPE optimizer.recommendation_status AS ENUM ('proposed', 'validated', 'rejected', 'sensitive', 'decommission');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Analysis status enum
DO $$ BEGIN
    CREATE TYPE optimizer.analysis_status AS ENUM ('running', 'completed', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Trend direction enum
DO $$ BEGIN
    CREATE TYPE optimizer.trend_direction AS ENUM ('growing', 'stable', 'declining', 'insufficient_data');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Onboarding status enum
DO $$ BEGIN
    CREATE TYPE optimizer.onboarding_status AS ENUM ('pending', 'configured', 'active', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================
-- Create Tables (Basic structure for Lot 1)
-- ============================================

-- Tenant clients table
CREATE TABLE IF NOT EXISTS optimizer.tenant_clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(2) NOT NULL DEFAULT 'FR',
    language VARCHAR(5) NOT NULL DEFAULT 'fr-FR',
    onboarding_status optimizer.onboarding_status DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tenant app registrations table
CREATE TABLE IF NOT EXISTS optimizer.tenant_app_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_client_id UUID NOT NULL REFERENCES optimizer.tenant_clients(id) ON DELETE CASCADE,
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
CREATE TABLE IF NOT EXISTS optimizer.analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_client_id UUID NOT NULL REFERENCES optimizer.tenant_clients(id) ON DELETE CASCADE,
    execution_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_seconds NUMERIC(10, 2),
    status optimizer.analysis_status DEFAULT 'running',
    total_monthly_savings NUMERIC(10, 2),
    total_annual_savings NUMERIC(10, 2),
    cohort_stats JSONB,
    cleanup_stats JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
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
-- Create Indexes
-- ============================================

-- Tenant clients indexes
CREATE INDEX IF NOT EXISTS idx_tenant_clients_tenant_id ON optimizer.tenant_clients(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_clients_status ON optimizer.tenant_clients(onboarding_status);
CREATE INDEX IF NOT EXISTS idx_tenant_clients_country ON optimizer.tenant_clients(country);
CREATE INDEX IF NOT EXISTS idx_tenant_clients_created_at ON optimizer.tenant_clients(created_at);

-- Tenant app registrations indexes
CREATE INDEX IF NOT EXISTS idx_tenant_app_tenant_client ON optimizer.tenant_app_registrations(tenant_client_id);
CREATE INDEX IF NOT EXISTS idx_tenant_app_valid ON optimizer.tenant_app_registrations(is_valid);

-- Analyses indexes
CREATE INDEX IF NOT EXISTS idx_analyses_tenant_client ON optimizer.analyses(tenant_client_id);
CREATE INDEX IF NOT EXISTS idx_analyses_execution_date ON optimizer.analyses(execution_date DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON optimizer.analyses(status);

-- Audit logs indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON optimizer.audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table ON optimizer.audit_logs(table_name);

-- ============================================
-- Create Functions and Triggers
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION optimizer.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to tables with updated_at column
DROP TRIGGER IF EXISTS update_tenant_clients_updated_at ON optimizer.tenant_clients;
CREATE TRIGGER update_tenant_clients_updated_at 
    BEFORE UPDATE ON optimizer.tenant_clients 
    FOR EACH ROW EXECUTE FUNCTION optimizer.update_updated_at_column();

DROP TRIGGER IF EXISTS update_tenant_app_registrations_updated_at ON optimizer.tenant_app_registrations;
CREATE TRIGGER update_tenant_app_registrations_updated_at 
    BEFORE UPDATE ON optimizer.tenant_app_registrations 
    FOR EACH ROW EXECUTE FUNCTION optimizer.update_updated_at_column();

-- ============================================
-- Create Database Roles and Permissions
-- ============================================

-- Create application role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'm365_app_user') THEN
        CREATE ROLE m365_app_user;
    END IF;
END
$$;

-- Create readonly role for reporting/analytics
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'm365_readonly') THEN
        CREATE ROLE m365_readonly;
    END IF;
END
$$;

-- Grant permissions to application role
GRANT USAGE ON SCHEMA optimizer TO m365_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA optimizer TO m365_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA optimizer TO m365_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO m365_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT USAGE, SELECT ON SEQUENCES TO m365_app_user;

-- Grant permissions to readonly role
GRANT USAGE ON SCHEMA optimizer TO m365_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA optimizer TO m365_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA optimizer GRANT SELECT ON TABLES TO m365_readonly;

-- ============================================
-- Insert Test Data (for development)
-- ============================================

-- Insert sample tenant for testing
INSERT INTO optimizer.tenant_clients (tenant_id, name, country, language, onboarding_status, metadata)
VALUES 
    ('12345678-1234-1234-1234-123456789012', 'Contoso Ltd', 'FR', 'fr-FR', 'pending', '{"industry": "technology", "size": "medium"}'),
    ('87654321-4321-4321-4321-210987654321', 'Fabrikam Inc', 'US', 'en-US', 'pending', '{"industry": "manufacturing", "size": "large"}')
ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================
-- Create Views for Common Queries
-- ============================================

-- View for active tenants with latest analysis
CREATE OR REPLACE VIEW optimizer.v_tenant_summary AS
SELECT 
    tc.id,
    tc.tenant_id,
    tc.name,
    tc.country,
    tc.language,
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
-- Database Configuration and Comments
-- ============================================

-- Comment on schema and tables
COMMENT ON SCHEMA optimizer IS 'Main schema for M365 License Optimizer application';
COMMENT ON TABLE optimizer.tenant_clients IS 'Stores client tenant information for multitenant support';
COMMENT ON TABLE optimizer.tenant_app_registrations IS 'Stores Azure AD app registration credentials per tenant';
COMMENT ON TABLE optimizer.analyses IS 'Stores analysis execution history and results';
COMMENT ON TABLE optimizer.audit_logs IS 'Stores audit trail for GDPR compliance and security';

-- ============================================
-- Completion Message
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'M365 License Optimizer Database Initialized Successfully';
    RAISE NOTICE 'Schema: optimizer';
    RAISE NOTICE 'Tables: tenant_clients, tenant_app_registrations, analyses, audit_logs';
    RAISE NOTICE 'Roles: m365_app_user, m365_readonly';
    RAISE NOTICE 'Extensions: pgcrypto';
    RAISE NOTICE 'UUID Generation: gen_random_uuid()';
    RAISE NOTICE '========================================';
END
$$;
