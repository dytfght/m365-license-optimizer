"""
API v1 router aggregation
"""
from fastapi import APIRouter

from .endpoints import auth, health, tenants

# Create v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(tenants.router)

# Health endpoints are included at root level in main.py
# but we can also include them here for /api/v1/health
# (health.router is included in main.py at root level)

__all__ = ["api_router"]
