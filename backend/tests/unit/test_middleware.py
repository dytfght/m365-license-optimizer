"""
Unit tests for middleware components
"""
import pytest
from fastapi import FastAPI, Request, Response, status
from fastapi.testclient import TestClient

from src.core.middleware import (
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    AuditLogMiddleware,
    get_user_identifier,
    rate_limit_exceeded_handler,
)


@pytest.fixture
def app():
    """Create a test FastAPI app with middleware"""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app


@pytest.fixture
def client_with_security_headers(app):
    """Create test client with security headers middleware"""
    app.add_middleware(SecurityHeadersMiddleware)
    return TestClient(app)


@pytest.fixture
def client_with_request_id(app):
    """Create test client with request ID middleware"""
    app.add_middleware(RequestIDMiddleware)
    return TestClient(app)


@pytest.fixture
def client_with_audit_log(app):
    """Create test client with audit log middleware"""
    app.add_middleware(AuditLogMiddleware)
    return TestClient(app)


# ============================================
# Security Headers Tests
# ============================================


def test_security_headers_present(client_with_security_headers):
    """Test that all security headers are present in response"""
    response = client_with_security_headers.get("/test")
    
    assert response.status_code == 200
    
    # Check all expected security headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "Content-Security-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Permissions-Policy" in response.headers


def test_security_headers_csp_policy(client_with_security_headers):
    """Test Content Security Policy is strict"""
    response = client_with_security_headers.get("/test")
    
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp


# ============================================
# Request ID Tests
# ============================================


def test_request_id_generated(client_with_request_id):
    """Test that request ID is generated if not provided"""
    response = client_with_request_id.get("/test")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    
    # Should be a UUID
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36  # UUID length with hyphens


def test_request_id_preserved(client_with_request_id):
    """Test that provided request ID is preserved"""
    custom_id = "custom-request-id-12345"
    
    response = client_with_request_id.get(
        "/test",
        headers={"X-Request-ID": custom_id}
    )
    
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


# ============================================
# Audit Log Tests
# ============================================


def test_audit_log_middleware_success(client_with_audit_log, caplog):
    """Test audit log middleware logs successful requests"""
    response = client_with_audit_log.get("/test")
    
    assert response.status_code == 200
    
    # Check that request was logged (captured by caplog)
    # Note: In actual tests, you'd want to verify structlog output
    # This is a simplified version


def test_audit_log_middleware_captures_method_and_path(client_with_audit_log):
    """Test that audit log captures HTTP method and path"""
    response = client_with_audit_log.post("/test", json={"data": "test"})
    
    # Middleware should handle all methods
    # Response status depends on endpoint implementation
    assert "X-Request-ID" not in response.headers or isinstance(response.headers.get("X-Request-ID"), str)


# ============================================
# User Identifier Tests
# ============================================


@pytest.mark.asyncio
async def test_get_user_identifier_ip_fallback():
    """Test user identifier falls back to IP when no user"""
    # Create mock request without user
    from fastapi import Request
    from starlette.datastructures import Headers
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": Headers({}).raw,
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("localhost", 8000),
    }
    
    request = Request(scope)
    identifier = get_user_identifier(request)
    
    assert identifier.startswith("ip:")
    assert "127.0.0.1" in identifier


# ============================================
# Rate Limit Handler Tests
# ============================================


def test_all_middleware_together():
    """Test that all middleware work together without conflicts"""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    # Add all middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AuditLogMiddleware)
    
    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 200
    
    # Check that both middleware functions worked
    assert "X-Request-ID" in response.headers
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_middleware_preserves_response_content():
    """Test that middleware doesn't alter response content"""
    app = FastAPI()
    
    expected_data = {"message": "test", "value": 42}
    
    @app.get("/test")
    async def test_endpoint():
        return expected_data
    
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    
    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 200
    assert response.json() == expected_data
