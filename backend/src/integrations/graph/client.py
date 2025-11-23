"""
GR02, GR03, GR06: Microsoft Graph API client with retry logic
"""
from typing import Any, Optional

import aiohttp
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.config import settings

from .exceptions import GraphAPIError, GraphThrottlingError

logger = structlog.get_logger(__name__)


class GraphClient:
    """
    Microsoft Graph API client with automatic pagination and retry logic.
    Implements throttling handling as per Section 3.1.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = settings.GRAPH_API_BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for Graph API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "ConsistencyLevel": "eventual",
        }

    @retry(
        retry=retry_if_exception_type(GraphThrottlingError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=32),
        reraise=True,
    )
    async def _make_request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """
        Make HTTP request to Graph API with retry on throttling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL or path (relative to base_url)
            **kwargs: Additional arguments for aiohttp request

        Returns:
            Response JSON

        Raises:
            GraphThrottlingError: On HTTP 429 (will trigger retry)
            GraphAPIError: On other errors
        """
        if not url.startswith("http"):
            url = f"{self.base_url}/{url.lstrip('/')}"

        session = await self._get_session()
        headers = self._get_headers()
        headers.update(kwargs.pop("headers", {}))

        try:
            async with session.request(method, url, headers=headers, **kwargs) as resp:
                # Handle throttling (429)
                if resp.status == 429:
                    retry_after = int(resp.headers.get("Retry-After", 2))
                    logger.warning(
                        "graph_api_throttled", url=url, retry_after=retry_after
                    )
                    raise GraphThrottlingError(
                        f"Rate limit exceeded, retry after {retry_after}s",
                        retry_after=retry_after,
                    )

                # Handle other errors
                if resp.status >= 400:
                    error_data = (
                        await resp.json()
                        if resp.content_type == "application/json"
                        else {}
                    )
                    error_msg = error_data.get("error", {}).get(
                        "message", "Unknown error"
                    )

                    logger.error(
                        "graph_api_error",
                        url=url,
                        status_code=resp.status,
                        error=error_msg,
                    )

                    raise GraphAPIError(
                        f"Graph API error: {error_msg}",
                        status_code=resp.status,
                        response_data=error_data,
                    )

                # Success
                data = await resp.json()
                return data  # type: ignore[no-any-return]

        except aiohttp.ClientError as e:
            logger.error("graph_api_request_failed", url=url, error=str(e))
            raise GraphAPIError(f"Network error: {str(e)}")

    async def get(self, path: str, params: Optional[dict] = None) -> dict:
        """GET request to Graph API"""
        return await self._make_request("GET", path, params=params)

    async def post(self, path: str, json_data: Optional[dict] = None) -> dict:
        """POST request to Graph API"""
        return await self._make_request("POST", path, json=json_data)

    async def get_paginated(
        self, path: str, params: Optional[dict] = None, max_pages: Optional[int] = None
    ) -> list[dict]:
        """
        Get all items from paginated endpoint.

        Args:
            path: API path
            params: Query parameters
            max_pages: Maximum number of pages to fetch (None = all)

        Returns:
            List of all items across pages
        """
        items: list[dict] = []
        url: Optional[str] = path
        page_count = 0

        if params is None:
            params = {}

        # Set top parameter for pagination (max 999 per Graph API)
        if "$top" not in params:
            params["$top"] = 999

        while url:
            page_count += 1

            if max_pages and page_count > max_pages:
                logger.info(
                    "graph_pagination_max_pages_reached",
                    path=path,
                    pages=page_count,
                    items=len(items),
                )
                break

            data = await self.get(url, params=params if page_count == 1 else None)

            # Extract items
            page_items = data.get("value", [])
            items.extend(page_items)

            # Get next page URL
            url = data.get("@odata.nextLink")

            logger.debug(
                "graph_pagination_page_fetched",
                path=path,
                page=page_count,
                items_in_page=len(page_items),
                total_items=len(items),
                has_next=bool(url),
            )

        logger.info(
            "graph_pagination_completed",
            path=path,
            total_pages=page_count,
            total_items=len(items),
        )

        return items

    # GR02: Get subscribed SKUs
    async def get_subscribed_skus(self) -> list[dict]:
        """
        Get all subscribed SKUs (licenses) for the tenant.

        Returns:
            List of SKU objects with purchased/consumed units
        """
        logger.info("graph_fetching_subscribed_skus")
        skus = await self.get_paginated("/subscribedSkus")
        logger.info("graph_subscribed_skus_fetched", count=len(skus))
        return skus

    # GR03: Get users with licenses
    async def get_users(
        self,
        select_fields: Optional[list[str]] = None,
        filter_query: Optional[str] = None,
    ) -> list[dict]:
        """
        Get all users from the tenant.

        Args:
            select_fields: Fields to select (default: basic fields + licenses)
            filter_query: OData filter expression

        Returns:
            List of user objects
        """
        if select_fields is None:
            select_fields = [
                "id",
                "userPrincipalName",
                "displayName",
                "accountEnabled",
                "assignedLicenses",
                "department",
                "jobTitle",
                "officeLocation",
            ]

        params = {
            "$select": ",".join(select_fields),
        }

        if filter_query:
            params["$filter"] = filter_query

        logger.info(
            "graph_fetching_users", select_fields=select_fields, filter=filter_query
        )
        users = await self.get_paginated("/users", params=params)
        logger.info("graph_users_fetched", count=len(users))

        return users

    # GR06: Get organization information
    async def get_organization(self) -> dict:
        """
        Get tenant organization information.
        Requires Organization.Read.All permission.

        Returns:
            Organization object with tenant details
        """
        logger.info("graph_fetching_organization")
        data = await self.get("/organization")
        orgs = data.get("value", [])

        if not orgs:
            raise GraphAPIError("No organization found in tenant")

        org = orgs[0]
        logger.info(
            "graph_organization_fetched",
            tenant_id=org.get("id"),
            display_name=org.get("displayName"),
        )

        return org  # type: ignore[no-any-return]

    async def get_user_member_of(self, user_id: str) -> list[dict]:
        """
        Get groups a user is member of.

        Args:
            user_id: User ID (Graph ID or UPN)

        Returns:
            List of group objects
        """
        params = {
            "$select": "id,displayName,groupTypes",
        }

        groups = await self.get_paginated(f"/users/{user_id}/memberOf", params=params)

        return groups
