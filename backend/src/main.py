"""
FastAPI application entry point
"""
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.tenants import router as tenants_router
from .core.config import settings
from .core.database import close_db, init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="M365 License Optimizer - Multitenant SaaS for Microsoft 365 license optimization",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup/shutdown events
@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("application_starting", version=settings.APP_VERSION)


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    await close_db()
    logger.info("application_stopped")


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }


@app.get("/version")
async def version():
    """Version endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Include routers
app.include_router(tenants_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
