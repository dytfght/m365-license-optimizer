"""
Pydantic schemas for JWT tokens and authentication
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Response model for login endpoint"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration time in seconds")


class TokenPayload(BaseModel):
    """JWT token payload model"""
    sub: str = Field(..., description="Subject (user ID)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field(..., description="Token type (access or refresh)")
    tenants: list[str] = Field(default_factory=list, description="List of tenant IDs user has access to")
    email: str | None = Field(None, description="User email")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration time in seconds")
