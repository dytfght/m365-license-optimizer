"""
Pytest configuration and fixtures for all tests
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.core.database import get_db
from src.core.security import create_access_token
from src.main import app
from src.models.base import Base

# Force Redis host to localhost for tests
# Force Redis host to localhost for tests
settings.REDIS_HOST = "localhost"
settings.APP_VERSION = "0.4.0"
settings.JWT_SECRET_KEY = "test-secret-key-123"
settings.JWT_ALGORITHM = "HS256"

# Use the main database (m365_optimizer) for tests
# Tables are created/dropped for each test to ensure isolation
TEST_DATABASE_URL = settings.DATABASE_URL


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """
    Create test database engine with proper cleanup.

    This fixture:
    1. Creates a clean database schema for each test
    2. Drops all tables and types after the test
    3. Handles PostgreSQL ENUM types properly with CASCADE
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Setup: Create clean schema
    async with engine.begin() as conn:
        # Drop schema cascade to handle orphaned tables from previous tests
        await conn.execute(text("DROP SCHEMA IF EXISTS optimizer CASCADE"))
        await conn.execute(text("CREATE SCHEMA optimizer"))

        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Teardown: Clean up all database objects
    try:
        async with engine.begin() as conn:
            # Drop the entire schema to clean up ENUMs and other types
            await conn.execute(text("DROP SCHEMA IF EXISTS optimizer CASCADE"))
            await conn.execute(text("CREATE SCHEMA optimizer"))
    except Exception as e:
        # Log the error but don't fail the test
        print(f"Warning: Error during database cleanup: {e}")
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session.

    Each test gets a fresh session that is rolled back after the test.
    This ensures test isolation.
    """
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client for API tests with database override.

    This fixture:
    1. Overrides the database dependency to use the test session
    2. Provides an AsyncClient for making API requests
    3. Cleans up overrides after the test
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(db_session):
    """
    Mock authentication headers for tests.

    Creates a test user in the database and returns headers with a valid Bearer token.
    """
    from uuid import uuid4

    from src.core.security import get_password_hash
    from src.models.tenant import TenantClient
    from src.models.user import User

    # Create a dummy tenant first
    tenant_id = uuid4()
    tenant = TenantClient(
        id=tenant_id,
        name="Test Tenant",
        tenant_id=str(uuid4()),  # Azure Tenant ID
        country="US",
        onboarding_status="active",
    )
    db_session.add(tenant)
    await db_session.flush()  # Flush to get the ID if needed

    user_id = uuid4()
    user = User(
        id=user_id,
        graph_id=str(uuid4()),
        tenant_client_id=tenant_id,
        user_principal_name="test@example.com",
        display_name="Test User",
        password_hash=get_password_hash("test-password"),
        account_enabled=True,
    )
    db_session.add(user)
    await db_session.commit()

    access_token = create_access_token(
        data={"sub": str(user_id), "email": "test@example.com"}
    )
    if isinstance(access_token, bytes):
        access_token = access_token.decode("utf-8")

    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_tenant_data():
    """
    Sample tenant data for testing.

    Returns a dictionary with valid tenant creation data.
    """
    return {
        "name": "Test Company",
        "azure_tenant_id": "12345678-1234-1234-1234-123456789012",
        "domain": "testcompany.onmicrosoft.com",
        "client_id": "app-client-id-123",
        "client_secret": "app-client-secret-456",
        "is_active": True,
    }


@pytest.fixture
def sample_user_data():
    """
    Sample user data for testing.

    Returns a dictionary with valid user data from Microsoft Graph.
    """
    return {
        "id": "user-graph-id-123",
        "userPrincipalName": "user@testcompany.onmicrosoft.com",
        "displayName": "Test User",
        "mail": "user@testcompany.com",
        "accountEnabled": True,
    }


# Cleanup hook to ensure database is clean before test session
@pytest.fixture(scope="session", autouse=True)
async def cleanup_database():
    """
    Clean up test database before and after all tests.

    This ensures a clean state even if previous test runs failed.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Cleanup before tests
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS optimizer CASCADE"))
            await conn.execute(text("CREATE SCHEMA optimizer"))
    except Exception as e:
        print(f"Warning: Error during initial cleanup: {e}")

    yield

    # Restore schema after all tests instead of dropping it
    # This allows infrastructure tests to pass after backend tests
    try:
        async with engine.begin() as conn:
            # Recreate schema for next use
            await conn.execute(text("DROP SCHEMA IF EXISTS optimizer CASCADE"))
            await conn.execute(text("CREATE SCHEMA optimizer"))
            # Recreate tables
            await conn.run_sync(Base.metadata.create_all)

            # Insert sample data for infrastructure tests
            await conn.execute(
                text(
                    """
                INSERT INTO optimizer.tenant_clients (id, tenant_id, name, country, onboarding_status)
                VALUES
                    (gen_random_uuid(), '12345678-1234-1234-1234-123456789012', 'Test Tenant 1', 'FR', 'active'),
                    (gen_random_uuid(), '87654321-4321-4321-4321-210987654321', 'Test Tenant 2', 'US', 'active')
                ON CONFLICT DO NOTHING;
            """
                )
            )
    except Exception as e:
        print(f"Warning: Error during final cleanup: {e}")
    finally:
        await engine.dispose()
