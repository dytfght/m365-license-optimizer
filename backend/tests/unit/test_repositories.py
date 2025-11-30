"""
Unit tests for repositories
"""
from uuid import uuid4

import pytest

from src.models.tenant import OnboardingStatus, TenantClient
from src.models.user import User
from src.repositories.tenant_repository import TenantRepository
from src.repositories.user_repository import UserRepository


@pytest.mark.unit
class TestTenantRepository:
    """Test TenantRepository"""

    @pytest.mark.asyncio
    async def test_create_tenant(self, db_session):
        """Test creating a tenant via repository"""
        repo = TenantRepository(db_session)

        tenant = await repo.create(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
            default_language="fr",
        )

        assert tenant.id is not None
        assert tenant.name == "Test Company"

    @pytest.mark.asyncio
    async def test_get_by_tenant_id(self, db_session):
        """Test getting tenant by Azure AD tenant ID"""
        repo = TenantRepository(db_session)

        tenant_id = str(uuid4())
        created_tenant = await repo.create(
            tenant_id=tenant_id,
            name="Test Company",
            country="FR",
        )
        await db_session.commit()

        # Retrieve by tenant_id
        retrieved = await repo.get_by_tenant_id(tenant_id)

        assert retrieved is not None
        assert retrieved.id == created_tenant.id
        assert retrieved.name == "Test Company"

    @pytest.mark.asyncio
    async def test_get_active_tenants(self, db_session):
        """Test getting only active tenants"""
        repo = TenantRepository(db_session)

        # Create active tenant
        await repo.create(
            tenant_id=str(uuid4()),
            name="Active Company",
            country="FR",
            onboarding_status=OnboardingStatus.ACTIVE,
        )

        # Create pending tenant
        await repo.create(
            tenant_id=str(uuid4()),
            name="Pending Company",
            country="US",
            onboarding_status=OnboardingStatus.PENDING,
        )

        await db_session.commit()

        active_tenants = await repo.get_active_tenants()

        # We assert that we have at least 1 active tenant.
        # Other tests might have created active tenants, so exact count check is risky in parallel exec
        assert len(active_tenants) >= 1
        # Check if our created tenant is in the list
        names = [t.name for t in active_tenants]
        assert "Active Company" in names
        assert "Pending Company" not in names

    @pytest.mark.asyncio
    async def test_create_with_app_registration(self, db_session):
        """Test creating tenant with app registration"""
        repo = TenantRepository(db_session)

        tenant_data = {
            "tenant_id": str(uuid4()),
            "name": "Test Company",
            "country": "FR",
        }

        app_reg_data = {
            "client_id": str(uuid4()),
            "client_secret_encrypted": "test-secret",
            "authority_url": "https://login.microsoftonline.com/test",
            "scopes": ["User.Read.All"],
        }

        tenant = await repo.create_with_app_registration(tenant_data, app_reg_data)
        await db_session.commit()

        assert tenant.id is not None
        assert tenant.app_registration is not None
        assert tenant.app_registration.client_id == app_reg_data["client_id"]


@pytest.mark.unit
class TestUserRepository:
    """Test UserRepository"""

    @pytest.mark.asyncio
    async def test_upsert_user_create(self, db_session):
        """Test upserting a new user"""
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        repo = UserRepository(db_session)

        user = await repo.upsert_user(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"john.doe.{uuid4()}@test.com",
            display_name="John Doe",
        )

        assert user.id is not None
        assert user.display_name == "John Doe"

    @pytest.mark.asyncio
    async def test_upsert_user_update(self, db_session):
        """Test upserting an existing user"""
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        repo = UserRepository(db_session)
        graph_id = str(uuid4())
        upn = f"john.doe.{uuid4()}@test.com"

        # Create user
        user1 = await repo.upsert_user(
            graph_id=graph_id,
            tenant_client_id=tenant.id,
            user_principal_name=upn,
            display_name="John Doe",
        )
        await db_session.commit()

        # Update same user
        user2 = await repo.upsert_user(
            graph_id=graph_id,
            tenant_client_id=tenant.id,
            user_principal_name=upn,
            display_name="John Doe Updated",
            department="IT",
        )
        await db_session.commit()

        assert user1.id == user2.id
        assert user2.display_name == "John Doe Updated"
        assert user2.department == "IT"

    @pytest.mark.asyncio
    async def test_sync_licenses(self, db_session):
        """Test syncing licenses (replace all)"""
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"john.doe.{uuid4()}@test.com",
        )
        db_session.add(user)
        await db_session.flush()

        repo = UserRepository(db_session)

        # Initial licenses
        licenses1 = [
            {"sku_id": str(uuid4()), "status": "active"},
            {"sku_id": str(uuid4()), "status": "active"},
        ]

        await repo.sync_licenses(user.id, licenses1)
        await db_session.commit()

        await db_session.refresh(user, ["license_assignments"])
        assert len(user.license_assignments) == 2

        # Update licenses (should replace)
        licenses2 = [
            {"sku_id": str(uuid4()), "status": "active"},
        ]

        await repo.sync_licenses(user.id, licenses2)
        await db_session.commit()

        await db_session.refresh(user, ["license_assignments"])
        assert len(user.license_assignments) == 1
        assert user.license_assignments[0].sku_id == licenses2[0]["sku_id"]
