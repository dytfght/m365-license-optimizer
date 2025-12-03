"""
API v1 router aggregation
"""
from fastapi import APIRouter

from .endpoints import (
    admin_sku_mapping,
    analyses,
    analytics,
    auth,
    graph,
    pricing,
    reports,
    reports,
    tenants,
    users,
)

# Create v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(graph.router)  # LOT4: Microsoft Graph sync endpoints
api_router.include_router(pricing.router)  # LOT5: Pricing import and queries
api_router.include_router(analyses.router)  # LOT6: License optimization analyses
api_router.include_router(reports.router)  # LOT7: PDF/Excel report generation
api_router.include_router(
    admin_sku_mapping.router
)  # LOT8: SKU mapping and add-on compatibility
api_router.include_router(
    analytics.router, prefix="/analytics", tags=["analytics"]
)  # Analytics endpoints
api_router.include_router(users.router)

# Health endpoints are included at root level in main.py
# but we can also include them here for /api/v1/health
# (health.router is included in main.py at root level)

__all__ = ["api_router"]
