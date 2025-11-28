"""
FastAPI application entry point for M365 License Optimizer
Lot 7: License optimization with PDF/Excel report generation
"""
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.deps import close_redis
from .api.v1 import api_router
from .api.v1.endpoints import health
from .core.config import settings
from .core.database import close_db
from .core.logging import configure_logging
from .core.middleware import (
    AuditLogMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TransactionMiddleware,
    limiter,
    rate_limit_exceeded_handler,
)

# Configure structured logging first
configure_logging()

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifespan: startup and shutdown events.
    """
    # === STARTUP ===
    logger.info(
        "application_starting",
        version=settings.APP_VERSION,
        lot=settings.LOT_NUMBER,
        environment=settings.ENVIRONMENT,
    )

    yield  # Application runs here

    # === SHUTDOWN ===
    logger.info("application_stopping")
    await close_db()
    await close_redis()
    logger.info("application_stopped")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for M365 License Optimizer",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(Exception, rate_limit_exceeded_handler)


# ============================================
# Middleware Registration (order matters!)
# ============================================
# 1. Request ID (first - sets up request context)
app.add_middleware(RequestIDMiddleware)

# 2. Security Headers (early - protects all responses)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Transaction Management
app.add_middleware(TransactionMiddleware)

# 4. Audit Logging (last - captures all request details)
app.add_middleware(AuditLogMiddleware)

# 5. CORS middleware (FastAPI built-in)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with structured logging"""
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


# Global exception handler for general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with structured logging"""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Root health check endpoint (no prefix)
app.include_router(health.router)

# Include API v1 router with prefix
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
async def root() -> dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "lot": settings.LOT_NUMBER,
        "docs": "/docs",
        "health": "/health",
        "api_version": "v1",
        "api_base": settings.API_V1_PREFIX,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
