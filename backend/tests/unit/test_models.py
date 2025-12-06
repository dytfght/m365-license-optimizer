"""
Unit tests for database models
"""
from uuid import uuid4

import pytest

from src.models.tenant import (
    ConsentStatus,
    OnboardingStatus,
    TenantAppRegistration,
    TenantClient,
)
from src.models.user import AssignmentSource, LicenseAssignment, LicenseStatus, User


@pytest.mark.unit
class TestTenantClientModel:
    """Test TenantClient model"""

    @pytest.mark.asyncio
    async def test_create_tenant_client(self, db_session):
        """Test creating a tenant client"""
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
            default_language="fr",
            onboarding_status=OnboardingStatus.PENDING,
        )

        db_session.add(tenant)
        await db_session.commit()
        await db_session.refresh(tenant)

        assert tenant.id is not None
        assert tenant.name == "Test Company"
        assert tenant.country == "FR"
        assert tenant.onboarding_status == OnboardingStatus.PENDING
        assert tenant.created_at is not None

    @pytest.mark.asyncio
    async def test_tenant_unique_tenant_id(self, db_session):
        """Test that tenant_id must be unique"""
        tenant_id = str(uuid4())

        tenant1 = TenantClient(
            tenant_id=tenant_id,
            name="Company 1",
            country="FR",
        )
        db_session.add(tenant1)
        await db_session.commit()

        # Try to create another tenant with same tenant_id
        tenant2 = TenantClient(
            tenant_id=tenant_id,
            name="Company 2",
            country="US",
        )
        db_session.add(tenant2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
        await db_session.rollback()


@pytest.mark.unit
class TestTenantAppRegistrationModel:
    """Test TenantAppRegistration model"""

    @pytest.mark.asyncio
    async def test_create_app_registration(self, db_session):
        """Test creating an app registration"""
        # Create tenant first
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create app registration
        app_reg = TenantAppRegistration(
            tenant_client_id=tenant.id,
            client_id=str(uuid4()),
            client_secret_encrypted="test-secret",
            authority_url="https://login.microsoftonline.com/test",
            scopes=["User.Read.All", "Directory.Read.All"],
            consent_status=ConsentStatus.PENDING,
        )

        db_session.add(app_reg)
        await db_session.commit()
        await db_session.refresh(app_reg)

        assert app_reg.id is not None
        assert app_reg.client_id is not None
        assert app_reg.scopes == ["User.Read.All", "Directory.Read.All"]
        assert app_reg.is_valid is False

    @pytest.mark.asyncio
    async def test_app_registration_relationship(self, db_session):
        """Test relationship between tenant and app registration"""
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        client_id = str(uuid4())
        app_reg = TenantAppRegistration(
            tenant_client_id=tenant.id,
            client_id=client_id,
            client_secret_encrypted="test-secret",
            authority_url="https://login.microsoftonline.com/test",
            scopes=["User.Read.All"],
        )
        db_session.add(app_reg)
        await db_session.commit()

        # Refresh with relationship
        await db_session.refresh(tenant, ["app_registration"])

        assert tenant.app_registration is not None
        assert tenant.app_registration.client_id == client_id


@pytest.mark.unit
class TestUserModel:
    """Test User model"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test creating a user"""
        # Create tenant first
        tenant = TenantClient(
            tenant_id=str(uuid4()),
            name="Test Company",
            country="FR",
        )
        db_session.add(tenant)
        await db_session.flush()

        # Create user
        user = User(
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=f"john.doe.{uuid4()}@testcompany.com",
            display_name="John Doe",
            account_enabled=True,
            department="IT",
            job_title="Developer",
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.graph_id is not None
        assert user.display_name == "John Doe"
        assert user.department == "IT"


@pytest.mark.unit
class TestLicenseAssignmentModel:
    """Test LicenseAssignment model"""

    @pytest.mark.asyncio
    async def test_create_license_assignment(self, db_session):
        """Test creating a license assignment"""
        # Setup tenant and user
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
            user_principal_name=f"john.doe.{uuid4()}@testcompany.com",
            display_name="John Doe",
        )
        db_session.add(user)
        await db_session.flush()

        # Create license assignment
        sku_id = str(uuid4())
        license = LicenseAssignment(
            user_id=user.id,
            sku_id=sku_id,
            status=LicenseStatus.ACTIVE,
            source=AssignmentSource.MANUAL,
        )

        db_session.add(license)
        await db_session.commit()
        await db_session.refresh(license)

        assert license.id is not None
        assert license.sku_id == sku_id
        assert license.status == LicenseStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_license_unique_constraint(self, db_session):
        """Test unique constraint on user_id + sku_id"""
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
            user_principal_name=f"john.doe.{uuid4()}@testcompany.com",
        )
        db_session.add(user)
        await db_session.flush()

        sku_id = str(uuid4())

        # First license
        license1 = LicenseAssignment(user_id=user.id, sku_id=sku_id)
        db_session.add(license1)
        await db_session.commit()

        # Try to add duplicate
        license2 = LicenseAssignment(user_id=user.id, sku_id=sku_id)
        db_session.add(license2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
        await db_session.rollback()
