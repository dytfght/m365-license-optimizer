"""
API v1 router aggregation
"""
from fastapi import APIRouter

from .endpoints import auth, graph, pricing, tenants

# Create v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(graph.router)  # LOT4: Microsoft Graph sync endpoints
api_router.include_router(pricing.router)  # LOT5: Pricing import and queries

# Health endpoints are included at root level in main.py
# but we can also include them here for /api/v1/health
# (health.router is included in main.py at root level)

__all__ = ["api_router"]
