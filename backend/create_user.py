import asyncio
import sys
from uuid import uuid4

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.core.security import get_password_hash
from src.models.tenant import TenantClient
from src.models.user import User

async def create_user(email: str, password: str):
    async with AsyncSessionLocal() as session:
        # Check if tenant exists, if not create one
        result = await session.execute(
            select(TenantClient).where(TenantClient.name == "Default Tenant")
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            tenant = TenantClient(
                id=uuid4(),
                name="Default Tenant",
                tenant_id=str(uuid4()),
                country="US",
                onboarding_status="active"
            )
            session.add(tenant)
            await session.commit()
            print(f"Created tenant: {tenant.id}")
        
        # Create user
        user = User(
            id=uuid4(),
            graph_id=str(uuid4()),
            tenant_client_id=tenant.id,
            user_principal_name=email,
            display_name="Admin User",
            account_enabled=True,
            password_hash=get_password_hash(password)
        )
        session.add(user)
        await session.commit()
        print(f"Created user: {email}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <email> <password>")
        sys.exit(1)
    
    asyncio.run(create_user(sys.argv[1], sys.argv[2]))
