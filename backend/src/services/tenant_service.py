"""
Business logic for tenant management
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..integrations.graph import GraphAuthService, GraphClient
from ..models.tenant import ConsentStatus, OnboardingStatus
from ..repositories.tenant_repository import TenantRepository

logger = structlog.get_logger(__name__)


class TenantService:
    """Service for tenant business logic"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TenantRepository(session)
        self.graph_auth = GraphAuthService()
    
    async def create_tenant(
        self,
        name: str,
        tenant_id: str,
        country: str,
        client_id: str,
        client_secret: str,
        scopes: list[str],
        default_language: str = "fr",
        csp_customer_id: Optional[str] = None
    ) -> dict:
        """
        Create a new tenant with app registration.
        
        Args:
            name: Tenant display name
            tenant_id: Azure AD Tenant ID
            country: ISO country code (FR, US, etc.)
            client_id: App Registration client ID
            client_secret: App Registration client secret
            scopes: List of Graph API scopes
            default_language: Default language (fr or en)
            csp_customer_id: Optional Partner Center customer ID
        
        Returns:
            dict with tenant info
        """
        # Check if tenant already exists
        existing = await self.repo.get_by_tenant_id(tenant_id)
        if existing:
            raise ValueError(f"Tenant {tenant_id} already exists")
        
        # Prepare data
        tenant_data = {
            "name": name,
            "tenant_id": tenant_id,
            "country": country,
            "default_language": default_language,
            "onboarding_status": OnboardingStatus.PENDING,
            "csp_customer_id": csp_customer_id,
        }
        
        authority_url = f"https://login.microsoftonline.com/{tenant_id}"
        
        app_reg_data = {
            "client_id": client_id,
            "client_secret": client_secret,  # TODO: Encrypt in production
            "authority_url": authority_url,
            "scopes": scopes,
            "consent_status": ConsentStatus.PENDING,
        }
        
        # Create tenant with app registration
        tenant = await self.repo.create_with_app_registration(
            tenant_data, app_reg_data
        )
        await self.session.commit()
        
        logger.info(
            "tenant_created",
            tenant_id=tenant.id,
            azure_tenant_id=tenant_id,
            name=name
        )
        
        return {
            "id": str(tenant.id),
            "name": tenant.name,
            "tenant_id": tenant.tenant_id,
            "status": tenant.onboarding_status.value,
        }
    
    async def validate_tenant_credentials(self, tenant_id: UUID) -> dict:
        """
        Validate tenant app registration credentials by attempting to get a token.
        
        Args:
            tenant_id: Internal tenant ID
        
        Returns:
            dict with validation result
        """
        tenant = await self.repo.get_with_app_registration(tenant_id)
        if not tenant or not tenant.app_registration:
            raise ValueError(f"Tenant {tenant_id} or app registration not found")
        
        app_reg = tenant.app_registration
        
        try:
            # Attempt to get token
            token = await self.graph_auth.get_token(
                tenant.tenant_id,
                app_reg.client_id,
                app_reg.client_secret
            )
            
            # Try to call Graph API to verify permissions
            graph_client = GraphClient(token)
            try:
                org = await graph_client.get_organization()
                
                # Update app registration status
                await self.repo.update_app_registration(
                    tenant_id,
                    is_valid=True,
                    last_validated_at=datetime.utcnow(),
                    consent_status=ConsentStatus.GRANTED,
                    consent_granted_at=datetime.utcnow()
                )
                
                # Update tenant status
                if tenant.onboarding_status == OnboardingStatus.PENDING:
                    await self.repo.update(tenant, onboarding_status=OnboardingStatus.ACTIVE)
                
                await self.session.commit()
                
                logger.info(
                    "tenant_credentials_validated",
                    tenant_id=tenant_id,
                    org_name=org.get("displayName")
                )
                
                return {
                    "valid": True,
                    "organization": org.get("displayName"),
                    "tenant_id": org.get("id"),
                }
            finally:
                await graph_client.close()
        
        except Exception as e:
            logger.error(
                "tenant_credentials_validation_failed",
                tenant_id=tenant_id,
                error=str(e)
            )
            
            # Update status
            await self.repo.update_app_registration(
                tenant_id,
                is_valid=False,
                consent_status=ConsentStatus.EXPIRED
            )
            await self.session.commit()
            
            return {
                "valid": False,
                "error": str(e),
            }
        finally:
            await self.graph_auth.close()
    
    async def get_all_tenants(self) -> list[dict]:
        """Get all tenants"""
        tenants = await self.repo.get_all(limit=1000)
        
        return [
            {
                "id": str(t.id),
                "name": t.name,
                "tenant_id": t.tenant_id,
                "country": t.country,
                "status": t.onboarding_status.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in tenants
        ]
    
    async def get_tenant_by_id(self, tenant_id: UUID) -> dict:
        """Get tenant by ID"""
        tenant = await self.repo.get_with_app_registration(tenant_id)
        
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        result = {
            "id": str(tenant.id),
            "name": tenant.name,
            "tenant_id": tenant.tenant_id,
            "country": tenant.country,
            "default_language": tenant.default_language,
            "status": tenant.onboarding_status.value,
            "created_at": tenant.created_at.isoformat(),
        }
        
        if tenant.app_registration:
            result["app_registration"] = {
                "client_id": tenant.app_registration.client_id,
                "consent_status": tenant.app_registration.consent_status.value,
                "is_valid": tenant.app_registration.is_valid,
                "last_validated_at": tenant.app_registration.last_validated_at.isoformat() if tenant.app_registration.last_validated_at else None,
            }
        
        return result
