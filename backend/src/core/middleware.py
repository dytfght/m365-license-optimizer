"""
Middleware for FastAPI application
Includes rate limiting, security headers, transaction management, and audit logging
"""
import time
from typing import Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

logger = structlog.get_logger(__name__)


# ============================================
# Rate Limiting
# ============================================


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Prioritizes user ID from token, falls back to IP address.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User identifier string
    """
    # Try to get user from request state (set by auth dependency)
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.id}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Create rate limiter instance using Redis
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[
        f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
        f"{settings.RATE_LIMIT_PER_DAY}/day",
    ],
    storage_uri=settings.REDIS_URL,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception
        
    Returns:
        JSON response with 429 status
    """
    logger.warning(
        "rate_limit_exceeded",
        path=request.url.path,
        identifier=get_user_identifier(request),
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail,
        },
    )


# ============================================
# Security Headers Middleware
# ============================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Implements OWASP security best practices.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy (strict for API)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # Permissions Policy (disable unnecessary features)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (if in production and using HTTPS)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# ============================================
# Request ID Middleware
# ============================================


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request.
    Useful for request tracing and debugging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request ID to request state and response headers.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with X-Request-ID header
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        
        # Store in request state for access in route handlers
        request.state.request_id = request_id
        
        # Bind to structlog context
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Clear context after request
            structlog.contextvars.clear_contextvars()


# ============================================
# Audit Log Middleware
# ============================================


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests for audit purposes.
    Logs request details, response status, and timing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from route handler
        """
        start_time = time.time()
        
        # Extract request details
        method = request.method
        path = request.url.path
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get user if authenticated
        user_id = None
        user_email = None
        user = getattr(request.state, "user", None)
        if user:
            user_id = str(user.id)
            user_email = user.email
        
        # Call next handler
        try:
            response = await call_next(request)
            status_code = response.status_code
            error_detail = None
        except Exception as e:
            status_code = 500
            error_detail = str(e)
            raise
        finally:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log audit event
            log_level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"
            log_func = getattr(logger, log_level)
            
            log_func(
                "api_request",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 2),
                client_ip=client_ip,
                user_agent=user_agent,
                user_id=user_id,
                user_email=user_email,
                error=error_detail,
            )
        
        return response


# ============================================
# Transaction Middleware
# ============================================


class TransactionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage database transactions automatically.
    Commits on success, rolls back on error.
    
    Note: This is a basic implementation. For production, consider
    using proper transaction scoping with dependencies.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Wrap request in database transaction.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response from route handler
        """
        # Only manage transactions for mutating operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Note: Transaction management is better handled at the repository level
            # or via dependencies. This middleware is a placeholder for demonstration.
            # In practice, transactions should be explicit in route handlers.
            logger.debug(
                "transaction_aware_request",
                method=request.method,
                path=request.url.path,
            )
        
        response = await call_next(request)
        return response


__all__ = [
    "limiter",
    "rate_limit_exceeded_handler",
    "SecurityHeadersMiddleware",
    "RequestIDMiddleware",
    "AuditLogMiddleware",
    "TransactionMiddleware",
]
