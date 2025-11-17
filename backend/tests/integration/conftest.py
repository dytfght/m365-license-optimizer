"""
Integration test fixtures
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.main import app
from src.core.database import get_db


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP client for integration tests with database override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {
        "Authorization": "Bearer test-token"
    }
