"""
Microsoft Graph API Service
Handles HTTP calls to Microsoft Graph endpoints with pagination,
retry logic, and error handling.
"""
import asyncio
import csv
import io
from typing import Any, Optional

import aiohttp
import structlog
from aiohttp import ClientError, ClientResponseError

from ..core.config import settings
from .graph_auth_service import GraphAuthService

logger = structlog.get_logger(__name__)


class GraphService:
    """
    Service for interacting with Microsoft Graph API.
    Handles users, licenses, and usage reports.
    """

    def __init__(self, graph_auth_service: GraphAuthService):
        """
        Initialize Graph service.

        Args:
            graph_auth_service: Service for acquiring access tokens
        """
        self.auth_service = graph_auth_service
        self.base_url = settings.GRAPH_API_BASE_URL
        self.timeout = settings.GRAPH_REQUEST_TIMEOUT
        self.max_retries = settings.GRAPH_MAX_RETRIES
        self.backoff_factor = settings.GRAPH_RETRY_BACKOFF_FACTOR

    async def fetch_users(self, tenant_id: str) -> list[dict]:
        """
        Fetch all users from Microsoft Graph.

        Args:
            tenant_id: Azure AD tenant ID

        Returns:
            List of user dictionaries

        Graph API:
            GET /users?$select=id,userPrincipalName,displayName,accountEnabled,
                               department,jobTitle,officeLocation,assignedLicenses
        """
        url = (
            f"{self.base_url}/users"
            "?$select=id,userPrincipalName,displayName,accountEnabled,"
            "department,jobTitle,officeLocation,assignedLicenses"
        )

        logger.info("fetching_users", tenant_id=tenant_id)
        users = await self._handle_pagination(tenant_id, url)
        logger.info("users_fetched", tenant_id=tenant_id, count=len(users))

        return users

    async def fetch_subscribed_skus(self, tenant_id: str) -> list[dict]:
        """
        Fetch subscribed SKUs (licenses) from Microsoft Graph.

        Args:
            tenant_id: Azure AD tenant ID

        Returns:
            List of SKU dictionaries

        Graph API:
            GET /subscribedSkus
        """
        url = f"{self.base_url}/subscribedSkus"

        logger.info("fetching_subscribed_skus", tenant_id=tenant_id)
        response = await self._make_request(tenant_id, url)

        skus = response.get("value", []) if isinstance(response, dict) else []
        logger.info("subscribed_skus_fetched", tenant_id=tenant_id, count=len(skus))

        return skus  # type: ignore[no-any-return]

    async def fetch_user_license_details(
        self, tenant_id: str, user_graph_id: str
    ) -> list[dict]:
        """
        Fetch license details for a specific user.

        Args:
            tenant_id: Azure AD tenant ID
            user_graph_id: Microsoft Graph user ID

        Returns:
            List of license detail dictionaries

        Graph API:
            GET /users/{id}/licenseDetails
        """
        url = f"{self.base_url}/users/{user_graph_id}/licenseDetails"

        try:
            response = await self._make_request(tenant_id, url)
            licenses = response.get("value", []) if isinstance(response, dict) else []
            return licenses  # type: ignore[no-any-return]
        except ClientResponseError as e:
            if e.status == 404:
                logger.warning(
                    "user_license_details_not_found",
                    tenant_id=tenant_id,
                    user_id=user_graph_id,
                )
                return []
            raise

    async def fetch_usage_report_email(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """
        Fetch email activity usage report.

        Args:
            tenant_id: Azure AD tenant ID
            period: Report period (D7, D28, D90, D180)

        Returns:
            List of email activity dictionaries

        Graph API:
            GET /reports/getEmailActivityUserDetail(period='D28')
        """
        url = f"{self.base_url}/reports/getEmailActivityUserDetail(period='{period}')"

        logger.info("fetching_email_usage_report", tenant_id=tenant_id, period=period)
        csv_content = await self._make_request(tenant_id, url, accept_csv=True)

        if isinstance(csv_content, str):
            data = self._parse_csv_report(csv_content)
            logger.info(
                "email_usage_report_fetched",
                tenant_id=tenant_id,
                period=period,
                count=len(data),
            )
            return data

        return []

    async def fetch_usage_report_onedrive(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """
        Fetch OneDrive activity usage report.

        Args:
            tenant_id: Azure AD tenant ID
            period: Report period (D7, D28, D90, D180)

        Returns:
            List of OneDrive activity dictionaries

        Graph API:
            GET /reports/getOneDriveActivityUserDetail(period='D28')
        """
        url = (
            f"{self.base_url}/reports/getOneDriveActivityUserDetail(period='{period}')"
        )

        logger.info(
            "fetching_onedrive_usage_report", tenant_id=tenant_id, period=period
        )
        csv_content = await self._make_request(tenant_id, url, accept_csv=True)

        if isinstance(csv_content, str):
            data = self._parse_csv_report(csv_content)
            logger.info(
                "onedrive_usage_report_fetched",
                tenant_id=tenant_id,
                period=period,
                count=len(data),
            )
            return data

        return []

    async def fetch_usage_report_sharepoint(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """
        Fetch SharePoint activity usage report.

        Args:
            tenant_id: Azure AD tenant ID
            period: Report period (D7, D28, D90, D180)

        Returns:
            List of SharePoint activity dictionaries

        Graph API:
            GET /reports/getSharePointActivityUserDetail(period='D28')
        """
        url = f"{self.base_url}/reports/getSharePointActivityUserDetail(period='{period}')"

        logger.info(
            "fetching_sharepoint_usage_report", tenant_id=tenant_id, period=period
        )
        csv_content = await self._make_request(tenant_id, url, accept_csv=True)

        if isinstance(csv_content, str):
            data = self._parse_csv_report(csv_content)
            logger.info(
                "sharepoint_usage_report_fetched",
                tenant_id=tenant_id,
                period=period,
                count=len(data),
            )
            return data

        return []

    async def fetch_usage_report_teams(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """
        Fetch Teams activity usage report.

        Args:
            tenant_id: Azure AD tenant ID
            period: Report period (D7, D28, D90, D180)

        Returns:
            List of Teams activity dictionaries

        Graph API:
            GET /reports/getTeamsUserActivityUserDetail(period='D28')
        """
        url = (
            f"{self.base_url}/reports/getTeamsUserActivityUserDetail(period='{period}')"
        )

        logger.info("fetching_teams_usage_report", tenant_id=tenant_id, period=period)
        csv_content = await self._make_request(tenant_id, url, accept_csv=True)

        if isinstance(csv_content, str):
            data = self._parse_csv_report(csv_content)
            logger.info(
                "teams_usage_report_fetched",
                tenant_id=tenant_id,
                period=period,
                count=len(data),
            )
            return data

        return []

    async def _make_request(
        self,
        tenant_id: str,
        url: str,
        method: str = "GET",
        accept_csv: bool = False,
    ) -> Any:
        """
        Make HTTP request to Microsoft Graph with retry logic.

        Args:
            tenant_id: Azure AD tenant ID
            url: Full URL to request
            method: HTTP method
            accept_csv: Whether to accept CSV response (for reports)

        Returns:
            Response data (dict or string for CSV)

        Raises:
            ClientResponseError: If request fails after retries
        """
        access_token = await self.auth_service.get_access_token(tenant_id)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "text/csv" if accept_csv else "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.request(
                        method, url, headers=headers
                    ) as response:
                        # Handle rate limiting (429)
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            logger.warning(
                                "graph_rate_limited",
                                tenant_id=tenant_id,
                                retry_after=retry_after,
                                attempt=attempt + 1,
                            )
                            await asyncio.sleep(retry_after)
                            continue

                        # Handle auth errors (401, 403)
                        if response.status in (401, 403):
                            logger.warning(
                                "graph_auth_error",
                                tenant_id=tenant_id,
                                status=response.status,
                                attempt=attempt + 1,
                            )
                            # Invalidate cache and retry
                            await self.auth_service.invalidate_cache(tenant_id)
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(self.backoff_factor**attempt)
                                continue

                        # Raise for other HTTP errors
                        response.raise_for_status()

                        # Return CSV content or JSON
                        if accept_csv:
                            return await response.text()
                        else:
                            return await response.json()

            except ClientError as e:
                logger.warning(
                    "graph_request_failed",
                    tenant_id=tenant_id,
                    url=url,
                    attempt=attempt + 1,
                    error=str(e),
                )

                # Retry with exponential backoff
                if attempt < self.max_retries - 1:
                    backoff_time = self.backoff_factor**attempt
                    await asyncio.sleep(backoff_time)
                else:
                    # Last attempt failed, raise
                    logger.error(
                        "graph_request_failed_all_retries",
                        tenant_id=tenant_id,
                        url=url,
                        error=str(e),
                    )
                    raise

        raise RuntimeError(f"Failed to make request after {self.max_retries} attempts")

    async def _handle_pagination(self, tenant_id: str, initial_url: str) -> list[dict]:
        """
        Handle Graph API pagination (@odata.nextLink).

        Args:
            tenant_id: Azure AD tenant ID
            initial_url: Initial URL to request

        Returns:
            Combined list of all paged results
        """
        all_items = []
        next_url: Optional[str] = initial_url

        while next_url:
            response = await self._make_request(tenant_id, next_url)

            if not isinstance(response, dict):
                break

            # Add items from this page
            items = response.get("value", [])
            all_items.extend(items)

            # Get next page URL
            next_url = response.get("@odata.nextLink")

            if next_url:
                logger.debug(
                    "graph_pagination_next_page",
                    tenant_id=tenant_id,
                    current_count=len(all_items),
                )

        return all_items

    def _parse_csv_report(self, csv_content: str) -> list[dict]:
        """
        Parse CSV report from Microsoft Graph.

        Args:
            csv_content: CSV string content

        Returns:
            List of dictionaries (one per row)
        """
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            data = list(reader)

            logger.debug("csv_report_parsed", row_count=len(data))
            return data

        except Exception as e:
            logger.error("csv_parsing_failed", error=str(e))
            return []
