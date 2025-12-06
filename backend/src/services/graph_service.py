"""
Microsoft Graph API Service
Handles HTTP calls to Microsoft Graph endpoints with pagination,
retry logic, and error handling.
"""
import csv
import io
from typing import Any

import structlog

from ..core.config import settings
from ..integrations.graph.client import GraphClient
from ..integrations.graph.exceptions import GraphAPIError
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

    async def _execute_with_client(
        self, tenant_id: str, operation: Any
    ) -> Any:
        """
        Execute a GraphClient operation with automatic token refresh on 401.

        Args:
            tenant_id: Azure AD tenant ID
            operation: Async function that takes a GraphClient and returns result

        Returns:
            Operation result
        """
        last_error = None

        for attempt in range(self.max_retries):
            client = None
            try:
                # Get token (cached or new)
                token = await self.auth_service.get_access_token(tenant_id)
                client = GraphClient(token)

                # Execute operation
                return await operation(client)

            except GraphAPIError as e:
                # Handle Auth errors (401, 403)
                if e.status_code in (401, 403):
                    logger.warning(
                        "graph_auth_error_retry",
                        tenant_id=tenant_id,
                        status=e.status_code,
                        attempt=attempt + 1
                    )
                    # Invalidate cache so next attempt gets fresh token
                    await self.auth_service.invalidate_cache(tenant_id)
                    last_error = e
                    continue

                # Re-raise other Graph errors
                raise

            except Exception as e:
                # Re-raise unexpected errors
                logger.error(
                    "graph_operation_failed",
                    tenant_id=tenant_id,
                    error=str(e)
                )
                raise

            finally:
                if client:
                    await client.close()

        # If we exhausted retries on auth error
        if last_error:
            raise last_error

        raise RuntimeError("Graph operation failed after retries")

    async def fetch_users(self, tenant_id: str) -> list[dict]:
        """
        Fetch all users from Microsoft Graph.
        """
        async def _op(client: GraphClient):
            return await client.get_users()

        logger.info("fetching_users", tenant_id=tenant_id)
        users = await self._execute_with_client(tenant_id, _op)
        logger.info("users_fetched", tenant_id=tenant_id, count=len(users))
        return users

    async def fetch_subscribed_skus(self, tenant_id: str) -> list[dict]:
        """
        Fetch subscribed SKUs (licenses) from Microsoft Graph.
        """
        async def _op(client: GraphClient):
            return await client.get_subscribed_skus()

        logger.info("fetching_subscribed_skus", tenant_id=tenant_id)
        skus = await self._execute_with_client(tenant_id, _op)
        logger.info("subscribed_skus_fetched", tenant_id=tenant_id, count=len(skus))
        return skus

    async def fetch_user_license_details(
        self, tenant_id: str, user_graph_id: str
    ) -> list[dict]:
        """
        Fetch license details for a specific user.
        """
        async def _op(client: GraphClient):
            return await client.get_user_license_details(user_graph_id)

        return await self._execute_with_client(tenant_id, _op)

    async def fetch_usage_report_email(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """Fetch email activity usage report."""
        return await self._fetch_report(tenant_id, "getEmailActivityUserDetail", period)

    async def fetch_usage_report_onedrive(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """Fetch OneDrive activity usage report."""
        return await self._fetch_report(tenant_id, "getOneDriveActivityUserDetail", period)

    async def fetch_usage_report_sharepoint(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """Fetch SharePoint activity usage report."""
        return await self._fetch_report(tenant_id, "getSharePointActivityUserDetail", period)

    async def fetch_usage_report_teams(
        self, tenant_id: str, period: str = "D28"
    ) -> list[dict]:
        """Fetch Teams activity usage report."""
        return await self._fetch_report(tenant_id, "getTeamsUserActivityUserDetail", period)

    async def _fetch_report(
        self, tenant_id: str, endpoint: str, period: str
    ) -> list[dict]:
        """Helper to fetch and parse usage reports"""
        async def _op(client: GraphClient):
            return await client.get_usage_report(endpoint, period)

        logger.info(f"fetching_{endpoint}", tenant_id=tenant_id, period=period)

        try:
            csv_content = await self._execute_with_client(tenant_id, _op)

            if isinstance(csv_content, str) and csv_content:
                data = self._parse_csv_report(csv_content)
                logger.info(
                    f"{endpoint}_fetched",
                    tenant_id=tenant_id,
                    period=period,
                    count=len(data),
                )
                return data
            return []

        except Exception as e:
            logger.error(f"failed_fetching_{endpoint}", error=str(e))
            # Return empty list on failure to not break full sync?
            # Original code logged error but didn't explicitly suppress all errors,
            # but _make_request raised.
            # However, sync_usage in endpoint catches exceptions per report?
            # No, sync_usage catches exception for the whole process.
            # Let's re-raise to be safe and consistent with previous behavior.
            raise

    def _parse_csv_report(self, csv_content: str) -> list[dict]:
        """
        Parse CSV report from Microsoft Graph.
        """
        try:
            # Remove BOM if present
            if csv_content.startswith("\ufeff"):
                csv_content = csv_content[1:]

            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            data = list(reader)

            logger.debug("csv_report_parsed", row_count=len(data))
            return data

        except Exception as e:
            logger.error("csv_parsing_failed", error=str(e))
            return []
