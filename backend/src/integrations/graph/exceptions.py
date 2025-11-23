"""
Microsoft Graph API exceptions
"""
from typing import Optional


class GraphAPIError(Exception):
    """Base exception for Graph API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class GraphAuthError(GraphAPIError):
    """Authentication/authorization errors"""

    pass


class GraphThrottlingError(GraphAPIError):
    """Rate limiting (HTTP 429) errors"""

    def __init__(self, message: str, retry_after: int = 2):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
