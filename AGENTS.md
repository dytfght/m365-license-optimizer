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

### Frontend (React/Next.js)
- **Framework**: Next.js 16.0.7 + React 19 + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query + Context API
- **HTTP Client**: Axios
- **Testing**: Jest + React Testing Library

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Azure Deployment**: Bicep templates for ARM deployment
- **Database Migrations**: Alembic
- **Monitoring**: Health checks, metrics, structured logging

## 📁 Project Structure

```
m365-license-optimizer/
├── backend/                          # FastAPI backend
│   ├── src/
│   │   ├── api/                     # REST endpoints (v1)
│   │   │   ├── endpoints/          # Route handlers
│   │   │   ├── schemas/            # Pydantic models
│   │   │   └── dependencies.py     # FastAPI dependencies
│   │   ├── core/                    # Core functionality
│   │   │   ├── config.py           # Settings management
│   │   │   ├── database.py         # SQLAlchemy setup
│   │   │   └── logging.py          # Structured logging
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── services/                # Business logic layer
│   │   ├── repositories/            # Data access layer
│   │   ├── integrations/            # External API integrations
│   │   │   ├── graph/              # Microsoft Graph client
│   │   │   └── partner/            # Partner Center client
│   │   └── utils/                   # Utility functions
│   ├── tests/                       # Test suites
│   │   ├── unit/                   # Unit tests
│   │   └── integration/            # Integration tests
│   ├── alembic/                     # Database migrations
│   └── requirements.txt             # Python dependencies
├── frontend/                        # Next.js frontend
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── pages/                  # Next.js pages/routes
│   │   ├── services/               # API integration
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── types/                  # TypeScript definitions
│   │   └── context/                # React contexts
│   ├── tests/                      # Frontend tests
│   └── package.json                # Node.js dependencies
├── docker/                         # Docker configurations
├── scripts/                        # Utility scripts
├── docs/                          # Documentation
└── docker-compose.yml             # Service orchestration
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

# Install dependencies
make setup-backend

# Run development server
make dev-backend

# Run tests
make test-backend

# Code quality
make lint-backend
make format-backend

# Database migrations
make migrate
```

### Frontend Development
```bash
cd frontend

# Install dependencies
make setup-frontend

# Run development server
make dev-frontend

# Build for production
make build-frontend

# Run tests
make test-frontend

# Lint code
make lint-frontend
```

### Docker Operations
```bash
# Build all images
make build-all

# Start/stop services
make up
make down
make restart

# View logs
make logs
make logs-backend
make logs-frontend

# Check service status
make status
```

## 🧪 Testing Strategy

### Backend Testing
- **Unit Tests**: `tests/unit/` - Test individual services and functions
- **Integration Tests**: `tests/integration/` - Test API endpoints and database operations
- **Test Configuration**: `pytest.ini` in `pyproject.toml`
- **Coverage**: HTML reports generated in `htmlcov/`
- **Mocking**: pytest-mock for external API calls

### Frontend Testing
- **Unit Tests**: Jest with React Testing Library
- **Test Files**: Co-located with components (`*.test.tsx`)
- **Configuration**: `jest.config.js`

### Running Tests
```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# Specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests only
pytest -v --cov=src --cov-report=html    # With coverage
```

## 🔒 Security & GDPR Compliance

### Security Features (Lot 10)
- **Authentication**: JWT tokens with secure password hashing (bcrypt)
- **Authorization**: Role-based access control
- **Encryption**: Client secrets encrypted with Fernet (AES-128)
- **Rate Limiting**: slowapi for API throttling
- **Security Headers**: Configured via middleware
- **Input Validation**: Pydantic models with strict validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

### GDPR Compliance
- **Data Retention**: Configurable log retention (default 90 days)
- **Right to be Forgotten**: API endpoint for data deletion
- **Data Export**: GDPR Article 20 compliance
- **Audit Logging**: All operations logged with user attribution
- **Consent Management**: Tenant-level consent tracking

### Security Commands
```bash
# Run security scan
make security-scan

# GDPR audit
make gdpr-audit

# Test security features
make test-lot10
```

## 📊 Deployment & Operations (Lot 11)

### Azure Deployment
- **Infrastructure as Code**: Bicep templates (`Main.bicep`)
- **Container Registry**: Azure Container Registry (ACR)
- **App Service**: Web Apps for Containers
- **Database**: Azure Database for PostgreSQL
- **Cache**: Azure Cache for Redis

### Deployment Commands
```bash
# Trigger Azure deployment
make deploy-azure

# Scale operations
make scale-up      # 3 backend replicas
make scale-down    # 1 backend replica

# Blue-green deployment
make blue-green
make blue-green-rollback

# Backup operations
make backup-db
make backup-db-azure
make restore-db
```

### Monitoring & Health
- **Health Checks**: `/health` and `/health/extended` endpoints
- **Metrics**: System metrics (CPU, RAM, disk) via `/admin/metrics`
- **Structured Logging**: JSON logs with correlation IDs
- **Audit Trail**: All operations logged with user context

## 🔑 Key Configuration

### Environment Variables
Critical variables in `.env` (copy from `.env.example`):
- **Database**: `POSTGRES_PASSWORD`, `DATABASE_URL`
- **Redis**: `REDIS_PASSWORD`
- **Azure AD**: `AZURE_AD_*` for Microsoft Graph access
- **Partner Center**: `PARTNER_*` for pricing data
- **Security**: `JWT_SECRET_KEY`, `ENCRYPTION_KEY`

### Required Azure App Registration
1. **Microsoft Graph Permissions**:
   - `User.Read.All`
   - `Organization.Read.All`
   - `Directory.Read.All`
   - `Reports.Read.All`
2. **Partner Center Access**: Delegated permissions for CSP operations

## 🎯 API Endpoints

### Core Functionality
```
POST /api/v1/auth/login                           # Authentication
GET  /api/v1/tenants                              # Tenant management
POST /api/v1/tenants/{id}/sync_users              # Sync users from Graph
POST /api/v1/tenants/{id}/sync_licenses           # Sync licenses
POST /api/v1/analyses/tenants/{id}/analyses       # Run optimization analysis
GET  /api/v1/analyses/analyses/{id}               # Get analysis results
POST /api/v1/reports/analyses/{id}/pdf            # Generate PDF report
POST /api/v1/reports/analyses/{id}/excel          # Generate Excel report
```

### Admin Operations
```
GET  /api/v1/admin/metrics                        # System metrics
GET  /api/v1/admin/health/extended                # Health status
GET  /api/v1/admin/logs                           # Audit logs
POST /api/v1/admin/backup                         # Manual backup
```

## 🧩 Development Guidelines

### Code Style
- **Backend**: Black formatter (88 char line length), Ruff linter, MyPy type checking
- **Frontend**: ESLint, TypeScript strict mode, Prettier formatting
- **Imports**: Organized with isort (Black profile)

### Database Conventions
- **Migrations**: Use Alembic with descriptive messages
- **Models**: SQLAlchemy declarative base with async support
- **Naming**: Snake_case for tables/columns, PascalCase for models
- **Indexes**: Created for frequently queried columns

### API Design
- **Versioning**: `/api/v1/` prefix for all endpoints
- **Response Format**: Consistent JSON with `data`/`error` structure
- **Error Handling**: Standardized HTTP status codes with detailed messages
- **Pagination**: Cursor-based for large datasets

### Git Workflow
1. Create feature branch: `git checkout -b feature/name`
2. Make changes with tests
3. Run quality checks: `make lint && make test`
4. Commit with descriptive messages
5. Push and create pull request

## 🚨 Important Notes

### Security
- Never commit `.env` files or sensitive data
- Use strong passwords (minimum 12 characters)
- Rotate encryption keys regularly
- Enable audit logging in production

### Performance
- Database queries use async SQLAlchemy
- Redis caching for frequently accessed data
- Pagination for large result sets
- Connection pooling configured

### Production
- Use Azure Managed Identity when possible
- Configure backup retention policies
- Set up monitoring alerts
- Use blue-green deployment for zero downtime

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

### Common Issues
1. **Database Connection**: Check `DATABASE_URL` in `.env`
2. **Redis Connection**: Verify `REDIS_PASSWORD` and network
3. **Azure AD Auth**: Ensure app registration has correct permissions
4. **Migration Failures**: Check Alembic history and database state
5. **Docker Issues**: Use `make clean-all` for complete reset

### Debug Commands
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:8000/health/extended

# View logs
docker-compose logs -f backend
docker-compose logs -f db

# Database access
docker exec -it m365_optimizer_db psql -U admin -d m365_optimizer

# Redis access
docker exec -it m365_optimizer_redis redis-cli -a $REDIS_PASSWORD
```

This project follows enterprise-grade development practices with comprehensive testing, security measures, and deployment automation. All code is written in French for consistency with the business domain and client requirements.