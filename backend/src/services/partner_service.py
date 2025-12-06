"""
Partner Center Service
Fetches pricing and subscription data from Partner Center API
"""
import json
from typing import Any

import aiohttp
import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .partner_auth_service import PartnerAuthService, PartnerCenterAuthError

logger = structlog.get_logger(__name__)


class PartnerCenterAPIError(Exception):
    """Exception raised for Partner Center API errors"""

    pass


class PartnerService:
    """
    Partner Center API client with pagination and retry logic

    Provides methods to fetch pricing and subscription data from
    Microsoft Partner Center API with automatic retry on failures,
    Redis caching, and pagination support.
    """

    BASE_URL = "https://api.partnercenter.microsoft.com/v1"
    CACHE_TTL_PRICING = 86400  # 24h for pricing data
    REQUEST_TIMEOUT = 30  # seconds

    def __init__(
        self, auth_service: PartnerAuthService, redis: Redis, db_session: AsyncSession
    ):
        self.auth = auth_service
        self.redis = redis
        self.db = db_session
        self.logger = logger.bind(service="partner_center")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, PartnerCenterAPIError)),
        reraise=True,
    )
    async def fetch_pricing(self, country: str) -> list[dict[str, Any]]:
        """
        Fetch pricing from Partner Center Rate Card API

        Args:
            country: ISO 3166-1 alpha-2 country code (e.g., 'FR', 'US')

        Returns:
            List of pricing offers

        Raises:
            PartnerCenterAPIError: If API request fails
            PartnerCenterAuthError: If authentication fails
        """
        # 1. Check Redis cache
        cache_key = f"partner_price:{country}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            self.logger.debug("partner_pricing_cache_hit", country=country)
            return json.loads(cached_data)  # type: ignore[no-any-return]

        # 2. Fetch from Partner Center API
        self.logger.info("partner_pricing_fetching", country=country)

        try:
            token = await self.auth.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            ) as session:
                # Note: Actual endpoint may vary - using ratecards as example
                url = f"{self.BASE_URL}/ratecards/azure"
                params = {"country": country}

                async with session.get(url, headers=headers, params=params) as response:
                    # Handle authentication errors
                    if response.status in (401, 403):
                        await self.auth.invalidate_token()
                        self.logger.warning(
                            "partner_auth_invalid", status=response.status
                        )
                        raise PartnerCenterAuthError(
                            f"Authentication failed: {response.status}"
                        )

                    # Handle rate limiting
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", "60")
                        self.logger.warning(
                            "partner_rate_limited", retry_after=retry_after
                        )
                        raise PartnerCenterAPIError(
                            f"Rate limited, retry after {retry_after}s"
                        )

                    # Raise for other errors
                    if response.status >= 400:
                        error_text = await response.text()
                        self.logger.error(
                            "partner_api_error",
                            status=response.status,
                            error=error_text[:500],
                        )
                        raise PartnerCenterAPIError(
                            f"API error {response.status}: {error_text[:200]}"
                        )

                    data = await response.json()

            # 3. Extract offers from response
            offers = data.get("offers", []) if isinstance(data, dict) else data

            # 4. Cache result
            await self.redis.setex(
                cache_key, self.CACHE_TTL_PRICING, json.dumps(offers)
            )

            self.logger.info(
                "partner_pricing_fetched", country=country, offers_count=len(offers)
            )

            return offers  # type: ignore[no-any-return]

        except (aiohttp.ClientError, PartnerCenterAuthError) as e:
            self.logger.error(
                "partner_pricing_fetch_error", error=str(e), exc_info=True
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, PartnerCenterAPIError)),
        reraise=True,
    )
    async def fetch_subscriptions(self, customer_id: str) -> list[dict[str, Any]]:
        """
        Fetch active subscriptions for a CSP customer

        Args:
            customer_id: Partner Center customer ID

        Returns:
            List of active subscriptions

        Raises:
            PartnerCenterAPIError: If API request fails
        """
        self.logger.info("partner_subscriptions_fetching", customer_id=customer_id)

        try:
            token = await self.auth.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            }

            subscriptions = []
            url = f"{self.BASE_URL}/customers/{customer_id}/subscriptions"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            ) as session:
                while url:
                    async with session.get(url, headers=headers) as response:
                        if response.status in (401, 403):
                            await self.auth.invalidate_token()
                            raise PartnerCenterAuthError(
                                f"Authentication failed: {response.status}"
                            )

                        if response.status >= 400:
                            error_text = await response.text()
                            raise PartnerCenterAPIError(
                                f"API error {response.status}: {error_text[:200]}"
                            )

                        data = await response.json()

                    # Add items to list
                    items = data.get("items", [])
                    subscriptions.extend(items)

                    # Handle pagination (@odata.nextLink)
                    url = data.get("@odata.nextLink") or data.get("nextLink")

            self.logger.info(
                "partner_subscriptions_fetched",
                customer_id=customer_id,
                count=len(subscriptions),
            )

            return subscriptions

        except (aiohttp.ClientError, PartnerCenterAuthError) as e:
            self.logger.error(
                "partner_subscriptions_fetch_error", error=str(e), exc_info=True
            )
            raise
