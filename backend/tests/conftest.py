"""
Optimized Pytest configuration for parallel testing with pytest-xdist
"""
import asyncio
import os
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.config import settings
from src.core.database import get_db
from src.core.security import create_access_token, get_password_hash
from src.main import app
from src.models.base import Base

# Test database configuration
TEST_DB_NAME = "m365_optimizer_test"
TEST_DATABASE_URL = settings.DATABASE_URL.replace("m365_optimizer", TEST_DB_NAME)

# Force test settings
settings.REDIS_HOST = "localhost"
settings.APP_VERSION = "0.7.0"
settings.LOT_NUMBER = 7
settings.JWT_SECRET_KEY = "test-secret-key-123-min-32-characters-long-for-security"
settings.JWT_ALGORITHM = "HS256"
settings.ENCRYPTION_KEY = "FhzMkaFPhMpiC9Eh3AkIDSDZEVA8QGMS7IId7NTX-B8="
settings.PARTNER_CLIENT_ID = "00000000-0000-0000-0000-000000000000"
settings.PARTNER_CLIENT_SECRET = "test-partner-secret"
settings.PARTNER_TENANT_ID = "00000000-0000-0000-0000-000000000000"

# Use test database URL
settings.DATABASE_URL = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Setup test database once per session for parallel testing.
    This creates a separate test database to avoid conflicts.
    """
    # Connect to the main database to create test database
    main_engine = create_async_engine(
        settings.DATABASE_URL.replace(TEST_DB_NAME, "m365_optimizer"),
        echo=False,
        isolation_level="AUTOCOMMIT",
    )

    try:
        async with main_engine.begin() as conn:
            # Create test database
            await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
            await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    except Exception as e:
        print(f"Warning: Could not create test database: {e}")
        # Fallback to using main database with unique schema
        TEST_DATABASE_URL = settings.DATABASE_URL
    finally:
        await main_engine.dispose()

    yield

    # Cleanup after all tests
    try:
        main_engine = create_async_engine(
            settings.DATABASE_URL.replace(TEST_DB_NAME, "m365_optimizer"),
            echo=False,
            isolation_level="AUTOCOMMIT",
        )
        async with main_engine.begin() as conn:
            await conn.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
    except Exception as e:
        print(f"Warning: Could not drop test database: {e}")
    finally:
        await main_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """
    Create test database engine for each test function.
    Uses transaction rollback for isolation instead of schema recreation.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Setup: Create schema and tables
    try:
        async with engine.begin() as conn:
            # Create schema first
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS optimizer"))

            # Set search_path so ENUMs are created in the optimizer schema
            await conn.execute(text("SET search_path TO optimizer, public"))

            # Extract all ENUM types from SQLAlchemy metadata
            # This automatically finds all ENUMs defined in models
            def create_enum_types(connection):
                from sqlalchemy.dialects.postgresql import ENUM

                # Collect all unique ENUM types from the metadata
                enum_types = {}
                for table in Base.metadata.tables.values():
                    for column in table.columns:
                        # Check if column type is a PostgreSQL ENUM
                        if isinstance(column.type, ENUM):
                            enum_name = column.type.name
                            if enum_name not in enum_types:
                                # Store the ENUM with its values
                                enum_types[enum_name] = column.type.enums

                # Manually add ENUMs with create_type=False
                # These are not auto-detected but are required
                if "snapshot_type" not in enum_types:
                    enum_types["snapshot_type"] = [
                        "license_inventory",
                        "user_inventory",
                        "service_usage",
                        "security_status",
                        "cost_analysis",
                        "optimization_recommendations",
                    ]
                if "metric_type" not in enum_types:
                    enum_types["metric_type"] = [
                        "license_utilization",
                        "license_cost",
                        "license_savings",
                        "license_efficiency",
                        "active_users",
                        "inactive_users",
                        "disabled_users",
                        "guest_users",
                        "exchange_usage",
                        "sharepoint_usage",
                        "teams_usage",
                        "onedrive_usage",
                        "mfa_coverage",
                        "risk_score",
                        "compliance_score",
                    ]
                if "licensestatus" not in enum_types:
                    enum_types["licensestatus"] = [
                        "ACTIVE",
                        "INACTIVE",
                        "SUSPENDED",
                        "PENDING",
                    ]
                if "assignmentsource" not in enum_types:
                    enum_types["assignmentsource"] = [
                        "AUTOMATIC",
                        "MANUAL",
                        "BULK",
                        "API",
                    ]

                # Create each ENUM type in the optimizer schema
                for enum_name, enum_values in enum_types.items():
                    values_str = ", ".join([f"'{value}'" for value in enum_values])
                    # Create the ENUM type if it doesn't exist
                    connection.execute(
                        text(
                            f"""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_type t
                                JOIN pg_namespace n ON t.typnamespace = n.oid
                                WHERE t.typname = '{enum_name}' AND n.nspname = 'optimizer'
                            ) THEN
                                CREATE TYPE {enum_name} AS ENUM ({values_str});
                            END IF;
                        END$$;
                    """
                        )
                    )

            # Create all ENUM types first
            await conn.run_sync(create_enum_types)

            # Now create all tables (ENUMs already exist)
            await conn.run_sync(Base.metadata.create_all)

    except Exception as e:
        print(f"Warning: Error during schema creation: {e}")
        # Continue even if there are errors

    yield engine

    # Cleanup
    try:
        await engine.dispose()
    except Exception as e:
        print(f"Warning: Error during engine disposal: {e}")


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session with transaction isolation.
    """
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client for API tests with database override.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(db_session, test_tenant):
    """
    Mock authentication headers for tests with admin privileges.
    """
    from uuid import uuid4

    from src.models.user import User

    user_id = uuid4()
    user = User(
        id=user_id,
        graph_id=str(uuid4()),
        tenant_client_id=test_tenant.id,
        user_principal_name="admin@example.com",
        display_name="Test Admin",
        password_hash=get_password_hash("test-password"),
        account_enabled=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Créer un token avec des claims d'admin
    access_token = create_access_token(
        data={
            "sub": str(user_id),
            "email": user.user_principal_name,
            "tenants": [str(test_tenant.id)],
        }
    )
    # Le token est déjà une string, pas besoin de décoder

    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for testing."""
    return {
        "name": "Test Company",
        "azure_tenant_id": "12345678-1234-1234-1234-123456789012",
        "domain": "testcompany.onmicrosoft.com",
        "country": "US",
        "is_active": True,
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user-graph-id-123",
        "userPrincipalName": "user@testcompany.onmicrosoft.com",
        "displayName": "Test User",
        "mail": "user@testcompany.com",
        "accountEnabled": True,
    }


@pytest_asyncio.fixture
async def test_tenant(db_session):
    """Create a test tenant for integration tests."""
    from uuid import uuid4

    from src.models.tenant import TenantClient

    tenant = TenantClient(
        id=uuid4(),
        name="Integration Test Tenant",
        tenant_id=str(uuid4()),
        country="US",
        onboarding_status="active",
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant


# Optimized for parallel testing
# Remove session-wide cleanup that causes conflicts
@pytest.fixture(scope="session", autouse=True)
def configure_parallel_testing():
    """Configure for parallel testing."""
    # Set environment variable to indicate parallel testing
    os.environ["PYTEST_XDIST_WORKER"] = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    yield
