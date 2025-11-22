"""
Integration tests for auth endpoints (login and refresh)
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.models.tenant import TenantClient
from src.models.user import User


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful login"""
        # Create a tenant
        tenant = TenantClient(
            tenant_id="test-tenant-123",
            name="Test Tenant",
            country="FR",
            onboarding_status="active",
        )
        db_session.add(tenant)
        await db_session.flush()
        
        # Create a user with password
        password = "SecurePassword123!"
        user = User(
            graph_id="user-graph-123",
            tenant_client_id=tenant.id,
            user_principal_name="user@test.com",
            display_name="Test User",
            account_enabled=True,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        
        # Test login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@test.com",  # OAuth2 uses 'username' field
                "password": password,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with wrong password"""
        # Create a tenant and user
        tenant = TenantClient(
            tenant_id="test-tenant-123",
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()
        
        password = "SecurePassword123!"
        user = User(
            graph_id="user-graph-123",
            tenant_client_id=tenant.id,
            user_principal_name="user@test.com",
            account_enabled=True,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        
        # Test login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@test.com",
                "password": "WrongPassword!",
            },
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client: AsyncClient):
        """Test login with non-existent user"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@test.com",
                "password": "password",
            },
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_disabled_account(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with disabled account"""
        # Create a tenant and disabled user
        tenant = TenantClient(
            tenant_id="test-tenant-123",
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()
        
        password = "SecurePassword123!"
        user = User(
            graph_id="user-graph-123",
            tenant_client_id=tenant.id,
            user_principal_name="user@test.com",
            account_enabled=False,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        
        # Test login
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@test.com",
                "password": password,
            },
        )
        
        assert response.status_code == 401
        assert "Account is disabled" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful token refresh"""
        # Create a tenant and user
        tenant = TenantClient(
            tenant_id="test-tenant-123",
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()
        
        password = "SecurePassword123!"
        user = User(
            graph_id="user-graph-123",
            tenant_client_id=tenant.id,
            user_principal_name="user@test.com",
            account_enabled=True,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        
        # Login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@test.com",
                "password": password,
            },
        )
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        
        # Test refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, client: AsyncClient, db_session: AsyncSession):
        """Test that refresh fails when using access token"""
        # Create a tenant and user
        tenant = TenantClient(
            tenant_id="test-tenant-123",
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()
        
        password = "SecurePassword123!"
        user = User(
            graph_id="user-graph-123",
            tenant_client_id=tenant.id,
            user_principal_name="user@test.com",
            account_enabled=True,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        
        # Login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "user@test.com",
                "password": password,
            },
        )
        access_token = login_response.json()["access_token"]
        
        # Try to refresh with access token (should fail)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        
        assert response.status_code == 401
