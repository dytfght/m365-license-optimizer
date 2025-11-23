"""
Application configuration using Pydantic Settings
"""
import os
from typing import Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../.env")
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env that aren't defined here
    )
    # Application
    APP_NAME: str = "M365 License Optimizer"
    APP_VERSION: str = "0.3.0"
    LOT_NUMBER: int = 3
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    # Database
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    DATABASE_URL: str
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    REDIS_URL: str = ""
    # Azure AD (Partner Authentication)
    AZURE_AD_TENANT_ID: str
    AZURE_AD_CLIENT_ID: str
    AZURE_AD_CLIENT_SECRET: str
    AZURE_AD_AUTHORITY: str = Field(default="")
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # API
    API_V1_PREFIX: str = "/api/v1"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_DAY: int = 1000
    # Microsoft Graph
    GRAPH_API_BASE_URL: str = "https://graph.microsoft.com/v1.0"
    GRAPH_API_SCOPES: str = "https://graph.microsoft.com/.default"

    @model_validator(mode="after")
    def assemble_connections(self) -> "Settings":
        # Interpolate DATABASE_URL if it contains placeholders
        if "%(POSTGRES_USER)s" in self.DATABASE_URL:
            self.DATABASE_URL = self.DATABASE_URL % {
                "POSTGRES_USER": self.POSTGRES_USER,
                "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
                "POSTGRES_HOST": self.POSTGRES_HOST,
                "POSTGRES_PORT": self.POSTGRES_PORT,
                "POSTGRES_DB": self.POSTGRES_DB,
            }
        # Interpolate AZURE_AD_AUTHORITY if it contains placeholder
        if "${AZURE_AD_TENANT_ID}" in self.AZURE_AD_AUTHORITY:
            self.AZURE_AD_AUTHORITY = self.AZURE_AD_AUTHORITY.replace(
                "${AZURE_AD_TENANT_ID}", self.AZURE_AD_TENANT_ID
            )
        # Fallback for AZURE_AD_AUTHORITY if still empty
        if not self.AZURE_AD_AUTHORITY:
            self.AZURE_AD_AUTHORITY = (
                f"https://login.microsoftonline.com/{self.AZURE_AD_TENANT_ID}"
            )

        # Construct REDIS_URL if not provided
        if not self.REDIS_URL:
            password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.REDIS_URL = f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

        return self

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


settings = Settings()
