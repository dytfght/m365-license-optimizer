# M365 License Optimizer - AI Agent Guide

## 🎯 Project Overview

M365 License Optimizer is a multi-tenant SaaS tool that enables Microsoft CSP/MPN partners to analyze Microsoft 365 license assignments, real service usage, and identify cost optimization opportunities. The project is built using a modern microservices architecture with Docker containerization.

**Key Features:**
- Multi-tenant license optimization analysis
- Microsoft Graph API integration for user/license data
- Partner Center API integration for pricing
- Automated report generation (PDF/Excel)
- GDPR compliance and security features
- Blue-green deployment capabilities

## 🏗️ Technology Stack

### Backend (Python/FastAPI)
- **Framework**: FastAPI 0.104.1 with Python 3.12
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0 (async)
- **Cache**: Redis 7 + aioredis
- **Authentication**: JWT (HS256) + OAuth2 Password Flow
- **API Documentation**: OpenAPI/Swagger auto-generated
- **Testing**: pytest with async support and coverage
- **Code Quality**: Black (88 char), Ruff linter, MyPy strict mode

### Frontend (React/Next.js)
- **Framework**: Next.js 16.0.7 + React 19 + TypeScript 5.3
- **Styling**: Tailwind CSS with custom blue color scheme (#0066CC)
- **State Management**: React Query (TanStack Query) + Context API
- **HTTP Client**: Axios with interceptors
- **Testing**: Jest + React Testing Library
- **Internationalization**: react-i18next (English/French)

### Infrastructure
- **Containerization**: Docker + Docker Compose with multi-stage builds
- **Azure Deployment**: Bicep templates for ARM deployment
- **Database Migrations**: Alembic with async support
- **Monitoring**: Health checks, metrics, structured JSON logging
- **Security**: Multi-layered middleware stack, rate limiting, encryption

## 📁 Project Structure

```
m365-license-optimizer/
├── backend/                          # FastAPI backend
│   ├── src/
│   │   ├── api/v1/                  # REST endpoints (v1)
│   │   │   ├── endpoints/          # Route handlers (auth, tenants, analyses, reports, admin)
│   │   │   ├── schemas/            # Pydantic models (request/response)
│   │   │   └── dependencies.py     # FastAPI dependency injection
│   │   ├── core/                    # Core functionality
│   │   │   ├── config.py           # Settings management (Pydantic)
│   │   │   ├── database.py         # SQLAlchemy 2.0 async setup
│   │   │   ├── logging.py          # Structured JSON logging (structlog)
│   │   │   └── middleware/         # Security, audit, rate limiting
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   └── base.py             # Base classes with UUID, timestamps
│   │   ├── services/                # Business logic layer
│   │   │   ├── tenant_service.py   # Multi-tenant operations
│   │   │   ├── analysis_service.py # License optimization logic
│   │   │   └── graph_service.py    # Microsoft Graph orchestration
│   │   ├── repositories/            # Data access layer (Repository pattern)
│   │   │   └── base_repository.py  # Generic CRUD operations
│   │   ├── integrations/            # External API integrations
│   │   │   ├── graph/              # Microsoft Graph client with retry logic
│   │   │   └── partner/            # Partner Center API client
│   │   └── utils/                   # Utility functions
│   ├── tests/                       # Test suites
│   │   ├── unit/                   # Unit tests for services
│   │   └── integration/            # API endpoint tests
│   ├── alembic/                     # Database migrations
│   ├── pyproject.toml              # Python tooling config (Black, Ruff, MyPy, pytest)
│   ├── requirements.txt            # Python dependencies
│   └── Dockerfile                   # Multi-stage build with security
├── frontend/                        # Next.js frontend
│   ├── src/
│   │   ├── components/             # React components (LoginForm, Navbar, etc.)
│   │   ├── pages/                  # Next.js pages (file-based routing)
│   │   │   ├── tenants/            # Tenant management pages
│   │   │   ├── analyses/           # Analysis pages
│   │   │   └── admin/              # Admin functionality
│   │   ├── services/               # API integration layer (Axios)
│   │   ├── hooks/                  # Custom React hooks
│   │   │   └── useRequireAuth.ts   # Authentication protection
│   │   ├── context/                # React Context providers
│   │   │   └── AuthContext.tsx     # Authentication state
│   │   ├── types/                  # TypeScript definitions
│   │   └── styles/                 # Global CSS
│   ├── tests/                      # Frontend tests (Jest + RTL)
│   ├── jest.config.js             # Jest configuration
│   ├── next.config.js             # Next.js config (standalone output)
│   ├── tailwind.config.js         # Tailwind CSS configuration
│   ├── tsconfig.json              # TypeScript configuration
│   ├── package.json               # Node.js dependencies
│   └── Dockerfile                  # Multi-stage production build
├── docker/                         # Docker configurations
│   └── db/init.sql                # Database initialization
├── scripts/                        # Utility scripts
│   ├── backup_db.py               # Database backup to Azure Blob
│   └── deploy_blue_green.sh       # Blue-green deployment
├── docs/                          # Documentation
├── reports/                       # Generated test coverage
├── logs/                          # Application logs
├── docker-compose.yml             # Service orchestration
├── Main.bicep                     # Azure Infrastructure as Code
├── Makefile                       # Unified build commands
└── .github/workflows/             # CI/CD pipelines
```

## 🔧 Development Commands

### Quick Start (Full Stack)
```bash
# Initial setup (creates .env, installs dependencies)
make setup

# Start all services with Docker
make up

# Or start infrastructure only (DB + Redis)
make start-infra

# Development mode (separate terminals)
make dev-backend    # Terminal 1: Backend on http://localhost:8000
make dev-frontend   # Terminal 2: Frontend on http://localhost:3001
```

### Backend Development
```bash
cd backend

# Install dependencies with virtual environment
make setup-backend

# Run development server with hot reload
make dev-backend

# Run tests with coverage
make test-backend

# Code quality tools
make lint-backend      # Ruff linter
make format-backend    # Black formatter + isort

# Database operations
make migrate          # Run Alembic migrations
make shell-backend    # Python shell with app context
```

### Frontend Development
```bash
cd frontend

# Install npm dependencies
make setup-frontend

# Run development server
make dev-frontend

# Build for production
make build-frontend

# Run tests
make test-frontend

# Lint code
make lint-frontend

# Type checking
npm run type-check
```

### Docker Operations
```bash
# Build all images with multi-stage optimization
make build-all

# Service management
make up               # Start all services
make down             # Stop all services
make restart          # Restart all services

# View logs
make logs             # All services
make logs-backend     # Backend only
make logs-frontend    # Frontend only

# Check service status and endpoints
make status

# Full cleanup (including database reset)
make clean-all
```

## 🧪 Testing Strategy

### Backend Testing Configuration
**pytest Configuration** (in `pyproject.toml`):
- **Test Discovery**: `test_*.py` files in `tests/` directory
- **Async Support**: `asyncio_mode = "auto"` for async tests
- **Coverage**: Branch coverage with HTML reports in `htmlcov/`
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- **Parallel Execution**: Configured but disabled due to concurrency issues

**Test Structure**:
```bash
tests/
├── unit/                    # Unit tests for individual services
│   ├── test_tenant_service.py
│   ├── test_analysis_service.py
│   └── test_security_service.py
└── integration/             # API endpoint integration tests
    ├── test_api_auth.py
    ├── test_api_tenants.py
    └── test_api_analyses.py
```

### Frontend Testing
**Jest Configuration** (`jest.config.js`):
- **Framework**: Next.js Jest configuration with jsdom environment
- **Testing Library**: React Testing Library for component testing
- **Module Mapping**: `@/` alias mapped to `src/`
- **Setup**: `jest.setup.js` for global test configuration

**Test Files**: Co-located with components using `*.test.tsx` pattern

### Running Tests
```bash
# All tests
make test

# Backend only with coverage
make test-backend

# Frontend only
make test-frontend

# Specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only
pytest -v --cov=src --cov-report=html    # With coverage report

# Security tests (Lot 10)
make test-lot10

# Deployment tests (Lot 11)
make test-lot11
```

## 🔒 Security & GDPR Compliance

### Security Architecture (Lot 10)
**Multi-Layered Security Stack**:
1. **Rate Limiting**: Redis-based with slowapi, user/IP identification
2. **Security Headers**: OWASP-compliant headers via middleware
3. **Request ID Tracking**: Unique correlation IDs for tracing
4. **Audit Logging**: Complete request/response audit trail
5. **Encryption Service**: Fernet (AES-128) for client secrets
6. **JWT Authentication**: HS256 tokens with secure password hashing (bcrypt)
7. **Input Validation**: Pydantic models with strict validation
8. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

**Security Features**:
- **Multi-Factor Authentication**: TOTP support with pyotp
- **Password Security**: Argon2 hashing for enhanced security
- **Client Secret Encryption**: Fernet encryption for Azure AD secrets
- **CORS Protection**: Configured for production environments
- **Request Validation**: Automatic validation with Pydantic schemas

### GDPR Compliance
- **Data Retention**: Configurable log retention (default 90 days)
- **Right to be Forgotten**: API endpoint for complete data deletion
- **Data Export**: GDPR Article 20 compliance with structured export
- **Audit Logging**: All operations logged with user attribution
- **Consent Management**: Tenant-level consent tracking
- **Encryption at Rest**: Database encryption and secure key management

### Security Commands
```bash
# Run security scan with Bandit
make security-scan

# GDPR compliance audit
make gdpr-audit

# Test security features specifically
make test-lot10
```

## 📊 Deployment & Operations (Lot 11)

### Azure Infrastructure
**Infrastructure as Code** (`Main.bicep`):
- **Azure Container Registry**: Standard tier for image storage
- **PostgreSQL Flexible Server**: Burstable B2s tier with PostgreSQL 16
- **Azure Cache for Redis**: Basic C0 tier (250MB)
- **App Service Plan**: Linux-based container hosting
- **Storage Account**: For database backups and deployment artifacts

**Blue-Green Deployment**: 
- Zero-downtime deployment strategy
- Traffic switching between environments
- Rollback capabilities
- Health check validation before traffic switch

### Deployment Pipeline
**GitHub Actions** (`.github/workflows/deploy-azure.yml`):
- **Multi-stage Pipeline**: Build, test, deploy, verify
- **Optional Database Backup**: Before deployment
- **Container Image Building**: Multi-stage Docker builds
- **Infrastructure Deployment**: Bicep template execution
- **Health Verification**: Automated health checks post-deployment

### Deployment Commands
```bash
# Trigger Azure deployment via GitHub Actions
make deploy-azure

# Manual scaling operations
make scale-up      # Scale backend to 3 replicas
make scale-down    # Scale backend to 1 replica

# Blue-green deployment
make blue-green           # Deploy new version
make blue-green-rollback  # Rollback to previous version

# Database operations
make backup-db         # Local database backup
make backup-db-azure   # Backup to Azure Blob Storage
make restore-db        # Interactive restore from backup
```

### Monitoring & Observability
**Health Checks**:
- **Basic Health**: `/health` - Service availability
- **Extended Health**: `/health/extended` - Database, Redis, external services
- **Docker Health**: Built-in container health checks

**Metrics & Logging**:
- **Structured Logging**: JSON logs with structlog
- **Request Tracing**: Correlation IDs for request tracking
- **Performance Metrics**: Response times, error rates, resource usage
- **Audit Trail**: Complete operation logging with user context

**Monitoring Endpoints**:
```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/extended

# System metrics (admin)
curl http://localhost:8000/api/v1/admin/metrics

# Audit logs (admin)
curl http://localhost:8000/api/v1/admin/logs
```

## 🔑 Key Configuration

### Environment Variables
**Critical Configuration** (copy from `.env.example`):
```bash
# Database
POSTGRES_DB=m365_optimizer
POSTGRES_USER=admin
POSTGRES_PASSWORD=SecurePass123!ChangeMe
DATABASE_URL=postgresql+asyncpg://admin:SecurePass123!ChangeMe@localhost:5432/m365_optimizer

# Redis
REDIS_PASSWORD=RedisSecurePass456!ChangeMe

# Security - MUST CHANGE
JWT_SECRET_KEY=CHANGE_ME_TO_A_RANDOM_SECRET_KEY_MIN_32_CHARS_LONG_PLEASE
ENCRYPTION_KEY=CHANGE_ME_TO_FERNET_KEY_32_BYTES_BASE64_ENCODED

# Azure AD (Partner Tenant)
AZURE_AD_TENANT_ID=00000000-0000-0000-0000-000000000000
AZURE_AD_CLIENT_ID=00000000-0000-0000-0000-000000000000
AZURE_AD_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE

# Partner Center API
PARTNER_CLIENT_ID=00000000-0000-0000-0000-000000000000
PARTNER_CLIENT_SECRET=YOUR_PARTNER_CLIENT_SECRET_HERE
PARTNER_TENANT_ID=00000000-0000-0000-0000-000000000000
```

### Required Azure App Registration
**Microsoft Graph Application Permissions**:
- `User.Read.All` - Read all users
- `Organization.Read.All` - Read organization information
- `Directory.Read.All` - Read directory data
- `Reports.Read.All` - Read usage reports

**Partner Center Access**: Delegated permissions for CSP operations

### Backend Configuration (`pyproject.toml`)
**Code Quality Tools**:
- **Black**: 88 character line length, Python 3.12 target
- **Ruff**: Fast Python linter with import sorting
- **MyPy**: Strict type checking with SQLAlchemy and Pydantic plugins
- **isort**: Black-compatible import sorting

**Testing Configuration**:
- **pytest**: Async support, coverage reporting, custom markers
- **Coverage**: Branch coverage with HTML reports
- **Parallel**: Configured but disabled due to concurrency issues

## 🎯 API Endpoints

### Core Functionality
```
POST /api/v1/auth/login                           # Authentication
GET  /api/v1/tenants                              # List tenants
POST /api/v1/tenants/{id}/sync_users              # Sync users from Graph
POST /api/v1/tenants/{id}/sync_licenses           # Sync licenses
POST /api/v1/analyses/tenants/{id}/analyses       # Run optimization analysis
GET  /api/v1/analyses/analyses/{id}               # Get analysis results
POST /api/v1/reports/analyses/{id}/pdf            # Generate PDF report
POST /api/v1/reports/analyses/{id}/excel          # Generate Excel report
```

### Admin Operations
```
GET  /api/v1/admin/metrics                        # System metrics (CPU, RAM, disk)
GET  /api/v1/admin/health/extended                # Extended health status
GET  /api/v1/admin/logs                           # Audit logs with filtering
POST /api/v1/admin/backup                         # Manual database backup
GET  /api/v1/admin/sku-mappings                   # SKU mapping management
```

## 🧩 Development Guidelines

### Code Style & Quality
**Backend Standards**:
- **Formatter**: Black with 88 character line length
- **Linter**: Ruff for fast linting and import sorting
- **Type Checking**: MyPy in strict mode with SQLAlchemy plugin
- **Imports**: Organized with isort (Black profile)
- **Async**: All database operations must be async
- **Error Handling**: Specific exception types with proper HTTP status codes

**Frontend Standards**:
- **TypeScript**: Strict mode enabled, comprehensive type definitions
- **Components**: Functional components with hooks
- **Styling**: Tailwind CSS utility-first approach
- **State Management**: React Query for server state, Context for client state
- **API Integration**: Centralized service layer with Axios interceptors

### Database Conventions
- **Migrations**: Alembic with descriptive messages and async support
- **Models**: SQLAlchemy declarative base with UUID primary keys
- **Naming**: Snake_case for tables/columns, PascalCase for models
- **Schema**: PostgreSQL schema `optimizer` for multi-tenancy
- **Indexes**: Created for frequently queried columns (tenant_id, email)
- **Timestamps**: Consistent `created_at`/`updated_at` with timezone support

### API Design Principles
- **Versioning**: `/api/v1/` prefix for all endpoints
- **Response Format**: Consistent JSON with `data`/`error` structure
- **Error Handling**: Standardized HTTP status codes with detailed messages
- **Pagination**: Cursor-based for large datasets
- **Authentication**: JWT Bearer tokens in Authorization header
- **Validation**: Pydantic models with automatic request validation

### Git Workflow
1. **Branch Creation**: `git checkout -b feature/descriptive-name`
2. **Development**: Make changes with comprehensive tests
3. **Quality Checks**: Run `make lint && make test` before commit
4. **Commit Messages**: Descriptive messages in French (project requirement)
5. **Pull Request**: Create PR with detailed description and test results

## 🚨 Important Notes

### Security Considerations
- **Environment Files**: Never commit `.env` files or sensitive data
- **Passwords**: Use strong passwords (minimum 12 characters)
- **Key Rotation**: Rotate encryption keys regularly
- **Audit Logging**: Enable comprehensive audit logging in production
- **Rate Limiting**: Configure appropriate rate limits for production
- **CORS**: Configure CORS properly for production domains

### Performance Optimization
- **Database**: Use async SQLAlchemy with connection pooling
- **Caching**: Redis caching for frequently accessed data
- **Pagination**: Implement pagination for all large result sets
- **Query Optimization**: Use proper database indexes and query planning
- **Connection Management**: Configure appropriate connection pool sizes

### Production Deployment
- **Managed Identity**: Use Azure Managed Identity when possible
- **Backup Policies**: Configure automated backup retention policies
- **Monitoring**: Set up comprehensive monitoring alerts
- **Deployment Strategy**: Use blue-green deployment for zero downtime
- **Scaling**: Configure auto-scaling based on metrics
- **Security**: Enable all security features and regular security scans

## 📚 Additional Documentation

Detailed validation documents for each lot:
- [LOT1-VALIDATION.md](./LOT1-VALIDATION.md) - Infrastructure Docker
- [LOT2-VALIDATION.md](./LOT2-VALIDATION.md) - Data Model
- [LOT3-VALIDATION.md](./LOT3-VALIDATION.md) - Backend API
- [LOT4-VALIDATION.md](./LOT4-VALIDATION.md) - Microsoft Graph
- [LOT5-VALIDATION.md](./LOT5-VALIDATION.md) - Partner Center
- [LOT6-VALIDATION.md](./LOT6-VALIDATION.md) - License Optimization
- [LOT7-VALIDATION.md](./LOT7-VALIDATION.md) - Report Generation
- [LOT8-VALIDATION.md](./LOT8-VALIDATION.md) - SKU Mapping & Add-ons
- [LOT10-VALIDATION.md](./LOT10-VALIDATION.md) - Security & GDPR
- [LOT11-VALIDATION.md](./LOT11-VALIDATION.md) - Deployment & Operations

## 🆘 Troubleshooting

### Common Issues & Solutions

1. **Database Connection Issues**:
   ```bash
   # Check DATABASE_URL in .env
   # Verify PostgreSQL is running: docker-compose ps
   # Test connection: docker exec -it m365_optimizer_db psql -U admin -d m365_optimizer
   ```

2. **Redis Connection Problems**:
   ```bash
   # Check REDIS_PASSWORD in .env
   # Test Redis connection: docker exec -it m365_optimizer_redis redis-cli -a $REDIS_PASSWORD ping
   ```

3. **Azure AD Authentication Failures**:
   ```bash
   # Verify app registration has required permissions
   # Check AZURE_AD_* variables in .env
   # Ensure client secret is properly encrypted
   ```

4. **Migration Failures**:
   ```bash
   # Check Alembic history: make shell-backend -> alembic history
   # Verify database state: alembic current
   # Reset if needed: make clean-all (⚠️ deletes all data)
   ```

5. **Docker Issues**:
   ```bash
   # Complete reset: make clean-all
   # Check logs: make logs
   # Rebuild images: make build-all
   # Check port conflicts: netstat -tulpn | grep -E '(8000|3000|5432|6379)'
   ```

### Debug Commands
```bash
# Service health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/extended

# View service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db

# Database access
docker exec -it m365_optimizer_db psql -U admin -d m365_optimizer

# Redis access
docker exec -it m365_optimizer_redis redis-cli -a $REDIS_PASSWORD

# Check running services
docker-compose ps

# View real-time logs
make logs
```

### Performance Debugging
```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# Monitor database queries (enable query logging)
# Add to backend/src/core/config.py: SQLALCHEMY_ECHO=True

# Check Redis cache hit rates
docker exec -it m365_optimizer_redis redis-cli -a $REDIS_PASSWORD info stats
```

This project follows enterprise-grade development practices with comprehensive testing, security measures, and deployment automation. All code is written in French for consistency with the business domain and client requirements. The architecture supports multi-tenant SaaS operations with robust security, GDPR compliance, and scalable deployment patterns.