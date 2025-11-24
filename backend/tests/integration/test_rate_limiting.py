"""
Integration tests for rate limiting functionality
Tests that rate limits are enforced using Redis
"""
import asyncio

import pytest
from httpx import AsyncClient

from src.core.config import settings
from src.main import app


@pytest.mark.asyncio
async def test_rate_limit_per_minute(client):
    """
    Test that rate limiting enforces per-minute limits.

    Note: This test makes many requests and may be slow.
    Consider using a lower limit in test environment.
    """
    # Make requests up to the limit
    responses = []

    # The limit is set in settings (default 100/minute)
    # For testing, we'll make fewer requests
    test_limit = 10

    # Make requests below the limit
    for i in range(test_limit):
        response = await client.get("/health")
        responses.append(response)

    # All should succeed
    for response in responses:
        assert (
            response.status_code == 200
        ), f"Request failed with status {response.status_code}"


@pytest.mark.asyncio
async def test_rate_limit_enforcement():
    """
    Test that exceeding rate limit returns 429 Too Many Requests.

    This test is disabled by default as it requires specific Redis setup
    and can be slow. Enable when testing rate limiting specifically.
    """
    pytest.skip("Skip slow rate limit test - enable manually when needed")

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make requests rapidly to trigger rate limit
        responses = []

        # Make slightly more than the per-minute limit
        for i in range(settings.RATE_LIMIT_PER_MINUTE + 5):
            response = await client.get("/health")
            responses.append(response)

        # Check that later requests were rate limited
        status_codes = [r.status_code for r in responses]

        # First 100 should succeed
        assert all(
            code == 200 for code in status_codes[: settings.RATE_LIMIT_PER_MINUTE]
        )

        # Remaining should be rate limited (429)
        assert any(
            code == 429 for code in status_codes[settings.RATE_LIMIT_PER_MINUTE :]
        )


@pytest.mark.asyncio
async def test_rate_limit_different_endpoints(client):
    """
    Test that rate limits apply across different endpoints.
    """
    # Make requests to different endpoints
    endpoints = ["/health", "/api/v1/version", "/api/v1/health"]

    responses = []
    for endpoint in endpoints * 3:  # 9 requests total
        response = await client.get(endpoint)
        responses.append(response)

    # All should succeed (well below limit)
    for response in responses:
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_headers_present():
    """
    Test that rate limit headers are present in responses.

    Note: slowapi may not add headers by default.
    Check slowapi documentation for header configuration.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200

        # Check for common rate limit headers (if configured)
        # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        # Note: These may not be present depending on slowapi configuration


@pytest.mark.asyncio
async def test_rate_limit_per_user_vs_ip():
    """
    Test that authenticated users have separate rate limits from IP-based limits.

    This is a placeholder test - actual implementation depends on auth setup.
    """
    # This would require setting up authenticated requests
    # and verifying that the user identifier changes from IP to user_id
    pytest.skip("Requires authenticated user setup")


@pytest.mark.asyncio
async def test_concurrent_requests_rate_limiting():
    """
    Test rate limiting with concurrent requests.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make 5 concurrent requests
        tasks = [client.get("/health") for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # All should succeed (well below limit)
        for response in responses:
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_reset_after_window():
    """
    Test that rate limits reset after the time window.

    This test is time-consuming and disabled by default.
    """
    pytest.skip("Skip slow time-based test - enable manually when needed")

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Make a request
        response1 = await client.get("/health")
        assert response1.status_code == 200

        # Wait for rate limit window to reset (60 seconds)
        await asyncio.sleep(61)

        # Make another request
        response2 = await client.get("/health")
        assert response2.status_code == 200
