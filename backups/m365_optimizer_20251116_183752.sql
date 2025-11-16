--
-- PostgreSQL database dump
--

\restrict wi9xLsWHdY6U3QdTJ36ZM33vxF3lsQRzvcg2l4CsIhMrD8w1JWBW8UtqhF5gTOF

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: optimizer; Type: SCHEMA; Schema: -; Owner: admin
--

CREATE SCHEMA optimizer;


ALTER SCHEMA optimizer OWNER TO admin;

--
-- Name: SCHEMA optimizer; Type: COMMENT; Schema: -; Owner: admin
--

COMMENT ON SCHEMA optimizer IS 'Main schema for M365 License Optimizer application';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA optimizer;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA optimizer;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: analysis_status; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.analysis_status AS ENUM (
    'running',
    'completed',
    'failed',
    'cancelled'
);


ALTER TYPE optimizer.analysis_status OWNER TO admin;

--
-- Name: assignment_source; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.assignment_source AS ENUM (
    'manual',
    'auto',
    'group_policy'
);


ALTER TYPE optimizer.assignment_source OWNER TO admin;

--
-- Name: license_status; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.license_status AS ENUM (
    'active',
    'suspended',
    'disabled',
    'trial'
);


ALTER TYPE optimizer.license_status OWNER TO admin;

--
-- Name: offer_type; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.offer_type AS ENUM (
    'new_commerce',
    'legacy',
    'csp'
);


ALTER TYPE optimizer.offer_type OWNER TO admin;

--
-- Name: onboarding_status; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.onboarding_status AS ENUM (
    'pending',
    'configured',
    'active',
    'error'
);


ALTER TYPE optimizer.onboarding_status OWNER TO admin;

--
-- Name: product_family; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.product_family AS ENUM (
    'business',
    'enterprise',
    'frontline',
    'education'
);


ALTER TYPE optimizer.product_family OWNER TO admin;

--
-- Name: recommendation_status; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.recommendation_status AS ENUM (
    'proposed',
    'validated',
    'rejected',
    'sensitive',
    'decommission'
);


ALTER TYPE optimizer.recommendation_status OWNER TO admin;

--
-- Name: trend_direction; Type: TYPE; Schema: optimizer; Owner: admin
--

CREATE TYPE optimizer.trend_direction AS ENUM (
    'growing',
    'stable',
    'declining',
    'insufficient_data'
);


ALTER TYPE optimizer.trend_direction OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: analyses; Type: TABLE; Schema: optimizer; Owner: admin
--

CREATE TABLE optimizer.analyses (
    id uuid DEFAULT optimizer.uuid_generate_v4() NOT NULL,
    tenant_client_id uuid NOT NULL,
    execution_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    duration_seconds numeric(10,2),
    status optimizer.analysis_status DEFAULT 'running'::optimizer.analysis_status,
    total_monthly_savings numeric(10,2),
    total_annual_savings numeric(10,2),
    cohort_stats jsonb,
    cleanup_stats jsonb,
    error_message text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE optimizer.analyses OWNER TO admin;

--
-- Name: TABLE analyses; Type: COMMENT; Schema: optimizer; Owner: admin
--

COMMENT ON TABLE optimizer.analyses IS 'Stores analysis execution history and results';


--
-- Name: audit_logs; Type: TABLE; Schema: optimizer; Owner: admin
--

CREATE TABLE optimizer.audit_logs (
    id uuid DEFAULT optimizer.uuid_generate_v4() NOT NULL,
    table_name character varying(100) NOT NULL,
    operation character varying(10) NOT NULL,
    old_data jsonb,
    new_data jsonb,
    user_name character varying(100),
    "timestamp" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE optimizer.audit_logs OWNER TO admin;

--
-- Name: tenant_app_registrations; Type: TABLE; Schema: optimizer; Owner: admin
--

CREATE TABLE optimizer.tenant_app_registrations (
    id uuid DEFAULT optimizer.uuid_generate_v4() NOT NULL,
    tenant_client_id uuid NOT NULL,
    client_id character varying(36) NOT NULL,
    client_secret_encrypted text,
    certificate_thumbprint character varying(255),
    authority_url character varying(500),
    scopes text[] DEFAULT ARRAY[]::text[],
    last_consent_date timestamp with time zone,
    is_valid boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE optimizer.tenant_app_registrations OWNER TO admin;

--
-- Name: TABLE tenant_app_registrations; Type: COMMENT; Schema: optimizer; Owner: admin
--

COMMENT ON TABLE optimizer.tenant_app_registrations IS 'Stores Azure AD app registration credentials per tenant';


--
-- Name: tenant_clients; Type: TABLE; Schema: optimizer; Owner: admin
--

CREATE TABLE optimizer.tenant_clients (
    id uuid DEFAULT optimizer.uuid_generate_v4() NOT NULL,
    tenant_id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    country character varying(2) DEFAULT 'FR'::character varying NOT NULL,
    language character varying(5) DEFAULT 'fr-FR'::character varying NOT NULL,
    onboarding_status optimizer.onboarding_status DEFAULT 'pending'::optimizer.onboarding_status,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE optimizer.tenant_clients OWNER TO admin;

--
-- Name: TABLE tenant_clients; Type: COMMENT; Schema: optimizer; Owner: admin
--

COMMENT ON TABLE optimizer.tenant_clients IS 'Stores client tenant information for multitenant support';


--
-- Data for Name: analyses; Type: TABLE DATA; Schema: optimizer; Owner: admin
--

COPY optimizer.analyses (id, tenant_client_id, execution_date, duration_seconds, status, total_monthly_savings, total_annual_savings, cohort_stats, cleanup_stats, error_message, created_at) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: optimizer; Owner: admin
--

COPY optimizer.audit_logs (id, table_name, operation, old_data, new_data, user_name, "timestamp") FROM stdin;
\.


--
-- Data for Name: tenant_app_registrations; Type: TABLE DATA; Schema: optimizer; Owner: admin
--

COPY optimizer.tenant_app_registrations (id, tenant_client_id, client_id, client_secret_encrypted, certificate_thumbprint, authority_url, scopes, last_consent_date, is_valid, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: tenant_clients; Type: TABLE DATA; Schema: optimizer; Owner: admin
--

COPY optimizer.tenant_clients (id, tenant_id, name, country, language, onboarding_status, metadata, created_at, updated_at) FROM stdin;
1a916412-2745-4edb-b851-bb42d4eaf083	12345678-1234-1234-1234-123456789012	Contoso Ltd	FR	fr-FR	pending	{"size": "medium", "industry": "technology"}	2025-11-16 17:31:03.804955+00	2025-11-16 17:31:03.804955+00
5ca6e8cc-518f-4e93-84be-1ba8b80eae0d	87654321-4321-4321-4321-210987654321	Fabrikam Inc	US	en-US	pending	{"size": "large", "industry": "manufacturing"}	2025-11-16 17:31:03.804955+00	2025-11-16 17:31:03.804955+00
\.


--
-- Name: analyses analyses_pkey; Type: CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.analyses
    ADD CONSTRAINT analyses_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: tenant_app_registrations tenant_app_registrations_pkey; Type: CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.tenant_app_registrations
    ADD CONSTRAINT tenant_app_registrations_pkey PRIMARY KEY (id);


--
-- Name: tenant_app_registrations tenant_app_registrations_tenant_client_id_client_id_key; Type: CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.tenant_app_registrations
    ADD CONSTRAINT tenant_app_registrations_tenant_client_id_client_id_key UNIQUE (tenant_client_id, client_id);


--
-- Name: tenant_clients tenant_clients_pkey; Type: CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.tenant_clients
    ADD CONSTRAINT tenant_clients_pkey PRIMARY KEY (id);


--
-- Name: tenant_clients tenant_clients_tenant_id_key; Type: CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.tenant_clients
    ADD CONSTRAINT tenant_clients_tenant_id_key UNIQUE (tenant_id);


--
-- Name: idx_analyses_execution_date; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_analyses_execution_date ON optimizer.analyses USING btree (execution_date DESC);


--
-- Name: idx_analyses_status; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_analyses_status ON optimizer.analyses USING btree (status);


--
-- Name: idx_analyses_tenant_client; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_analyses_tenant_client ON optimizer.analyses USING btree (tenant_client_id);


--
-- Name: idx_audit_logs_table; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_audit_logs_table ON optimizer.audit_logs USING btree (table_name);


--
-- Name: idx_audit_logs_timestamp; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_audit_logs_timestamp ON optimizer.audit_logs USING btree ("timestamp" DESC);


--
-- Name: idx_tenant_app_tenant_client; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_tenant_app_tenant_client ON optimizer.tenant_app_registrations USING btree (tenant_client_id);


--
-- Name: idx_tenant_app_valid; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_tenant_app_valid ON optimizer.tenant_app_registrations USING btree (is_valid);


--
-- Name: idx_tenant_clients_country; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_tenant_clients_country ON optimizer.tenant_clients USING btree (country);


--
-- Name: idx_tenant_clients_status; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_tenant_clients_status ON optimizer.tenant_clients USING btree (onboarding_status);


--
-- Name: idx_tenant_clients_tenant_id; Type: INDEX; Schema: optimizer; Owner: admin
--

CREATE INDEX idx_tenant_clients_tenant_id ON optimizer.tenant_clients USING btree (tenant_id);


--
-- Name: analyses analyses_tenant_client_id_fkey; Type: FK CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.analyses
    ADD CONSTRAINT analyses_tenant_client_id_fkey FOREIGN KEY (tenant_client_id) REFERENCES optimizer.tenant_clients(id) ON DELETE CASCADE;


--
-- Name: tenant_app_registrations tenant_app_registrations_tenant_client_id_fkey; Type: FK CONSTRAINT; Schema: optimizer; Owner: admin
--

ALTER TABLE ONLY optimizer.tenant_app_registrations
    ADD CONSTRAINT tenant_app_registrations_tenant_client_id_fkey FOREIGN KEY (tenant_client_id) REFERENCES optimizer.tenant_clients(id) ON DELETE CASCADE;


--
-- Name: SCHEMA optimizer; Type: ACL; Schema: -; Owner: admin
--

GRANT USAGE ON SCHEMA optimizer TO readonly;


--
-- Name: TABLE analyses; Type: ACL; Schema: optimizer; Owner: admin
--

GRANT SELECT ON TABLE optimizer.analyses TO readonly;


--
-- Name: TABLE audit_logs; Type: ACL; Schema: optimizer; Owner: admin
--

GRANT SELECT ON TABLE optimizer.audit_logs TO readonly;


--
-- Name: TABLE tenant_app_registrations; Type: ACL; Schema: optimizer; Owner: admin
--

GRANT SELECT ON TABLE optimizer.tenant_app_registrations TO readonly;


--
-- Name: TABLE tenant_clients; Type: ACL; Schema: optimizer; Owner: admin
--

GRANT SELECT ON TABLE optimizer.tenant_clients TO readonly;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: optimizer; Owner: admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA optimizer GRANT SELECT,USAGE ON SEQUENCES  TO readonly;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: optimizer; Owner: admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA optimizer GRANT SELECT ON TABLES  TO readonly;


--
-- PostgreSQL database dump complete
--

\unrestrict wi9xLsWHdY6U3QdTJ36ZM33vxF3lsQRzvcg2l4CsIhMrD8w1JWBW8UtqhF5gTOF

