"""
Pytest configuration and fixtures
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.models.base import Base

# Override settings for tests
settings.ENVIRONMENT = "test"
settings.DATABASE_URL = settings.DATABASE_URL.replace("m365_license_optimizer", "m365_license_optimizer_test")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()
