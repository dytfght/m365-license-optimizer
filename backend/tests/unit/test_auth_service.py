"""
Unit tests for auth_service (authentication service)
"""
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.models.tenant import TenantClient
from src.models.user import User
from src.services.auth_service import AuthenticationError, AuthService


@pytest.mark.unit
class TestAuthService:
    """Tests for AuthService"""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession):
        """Test successful user authentication"""
        # Create a tenant
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Tenant",
            country="FR",
            default_language="fr",
            onboarding_status="active",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create a user with password
        password = "SecurePassword123!"
        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"user_{uuid4()}@test.com",
            display_name="Test User",
            account_enabled=True,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()

        # Test authentication
        auth_service = AuthService(db_session)
        user_data = await auth_service.authenticate_user(
            user.user_principal_name, password
        )

        assert user_data is not None
        assert user_data["user_principal_name"] == user.user_principal_name
        assert user_data["display_name"] == "Test User"
        assert "id" in user_data

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession):
        """Test authentication with wrong password"""
        # Create a tenant
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create a user
        password = "SecurePassword123!"
        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"user_{uuid4()}@test.com",
            account_enabled=True,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()

        # Test with wrong password
        auth_service = AuthService(db_session)
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await auth_service.authenticate_user(
                user.user_principal_name, "WrongPassword!"
            )

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session: AsyncSession):
        """Test authentication with non-existent user"""
        auth_service = AuthService(db_session)

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            await auth_service.authenticate_user("nonexistent@test.com", "password")

    @pytest.mark.asyncio
    async def test_authenticate_disabled_account(self, db_session: AsyncSession):
        """Test authentication with disabled account"""
        # Create a tenant
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create a disabled user
        password = "SecurePassword123!"
        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"user_{uuid4()}@test.com",
            account_enabled=False,
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()

        # Test authentication
        auth_service = AuthService(db_session)
        with pytest.raises(AuthenticationError, match="Account is disabled"):
            await auth_service.authenticate_user(user.user_principal_name, password)

    @pytest.mark.asyncio
    async def test_create_tokens(self, db_session: AsyncSession):
        """Test token creation"""
        user_data = {
            "id": uuid4(),
            "user_principal_name": "user@test.com",
            "tenant_client_id": uuid4(),
            "display_name": "Test User",
        }

        auth_service = AuthService(db_session)
        tokens = await auth_service.create_tokens(user_data)

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, db_session: AsyncSession):
        """Test successful token refresh"""
        # Create a tenant
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create a user
        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"user_{uuid4()}@test.com",
            account_enabled=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Create tokens
        user_data = {
            "id": user.id,
            "user_principal_name": user.user_principal_name,
            "tenant_client_id": tenant.id,
            "display_name": "Test User",
        }
        auth_service = AuthService(db_session)
        tokens = await auth_service.create_tokens(user_data)

        # Refresh the token
        new_token_data = await auth_service.refresh_access_token(tokens.refresh_token)

        assert new_token_data["access_token"] is not None
        assert new_token_data["token_type"] == "bearer"
        assert new_token_data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, db_session: AsyncSession):
        """Test refresh with invalid token"""
        auth_service = AuthService(db_session)

        with pytest.raises(
            AuthenticationError, match="Invalid or expired refresh token"
        ):
            await auth_service.refresh_access_token("invalid.token.here")

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, db_session: AsyncSession):
        """Test that refresh fails when using access token instead of refresh token"""
        # Create a tenant and user
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Tenant",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"user_{uuid4()}@test.com",
            account_enabled=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Create tokens
        user_data = {
            "id": user.id,
            "user_principal_name": user.user_principal_name,
            "tenant_client_id": tenant.id,
            "display_name": "Test User",
        }
        auth_service = AuthService(db_session)
        tokens = await auth_service.create_tokens(user_data)

        # Try to refresh with access token (should fail)
        with pytest.raises(AuthenticationError, match="Invalid token type"):
            await auth_service.refresh_access_token(tokens.access_token)
