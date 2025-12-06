"""
Pydantic schemas for User models
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields"""

    user_principal_name: EmailStr = Field(
        ..., description="User principal name (email)"
    )
    display_name: str | None = Field(None, description="Display name")
    account_enabled: bool = Field(default=True, description="Account enabled status")
    department: str | None = Field(None, description="Department")
    job_title: str | None = Field(None, description="Job title")
    office_location: str | None = Field(None, description="Office location")


class UserLogin(BaseModel):
    """Login request schema"""

    email: EmailStr = Field(..., description="User email (UPN)")
    password: str = Field(..., min_length=8, description="User password")


class UserCreate(UserBase):
    """Schema for creating a new user"""

    graph_id: str = Field(..., description="Microsoft Graph user ID")
    tenant_client_id: UUID = Field(..., description="Tenant client ID")
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    display_name: str | None = None
    account_enabled: bool | None = None
    department: str | None = None
    job_title: str | None = None
    office_location: str | None = None


class UserResponse(UserBase):
    """Response schema for user data"""

    id: UUID = Field(..., description="User ID")
    graph_id: str = Field(..., description="Microsoft Graph user ID")
    tenant_client_id: UUID = Field(..., description="Tenant client ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """User schema with password hash (internal use only)"""

    password_hash: str = Field(..., description="Hashed password")
