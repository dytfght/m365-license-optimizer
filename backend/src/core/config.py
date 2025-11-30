"""
Application configuration using Pydantic Settings
"""
import os
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
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
    APP_VERSION: str = "0.8.0"
    LOT_NUMBER: int = 8
    API_V1_STR: str = "/api/v1"
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
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000",
        "http://localhost:8000/docs",
        "http://127.0.0.1:8000/docs",
        "http://0.0.0.0:8000/docs",
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

    # Microsoft Graph (LOT4)
    ENCRYPTION_KEY: str  # Fernet key for encrypting client secrets
    GRAPH_API_BASE_URL: str = "https://graph.microsoft.com/v1.0"
    GRAPH_API_SCOPES: list[str] = ["https://graph.microsoft.com/.default"]
    GRAPH_API_BETA_URL: str = "https://graph.microsoft.com/beta"
    GRAPH_API_AUTHORITY: str = "https://login.microsoftonline.com"
    GRAPH_MAX_RETRIES: int = 3
    GRAPH_RETRY_BACKOFF_FACTOR: int = 2
    GRAPH_REQUEST_TIMEOUT: int = 30

    # Microsoft Partner Center (LOT5)
    PARTNER_CLIENT_ID: str
    PARTNER_CLIENT_SECRET: str
    PARTNER_TENANT_ID: str
    PARTNER_AUTHORITY: str = ""

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """Validate Fernet encryption key format"""
        if not v or v == "CHANGE_ME_TO_FERNET_KEY_32_BYTES_BASE64_ENCODED":
            raise ValueError(
                "ENCRYPTION_KEY must be set in .env. "
                "This key is required to securely encrypt client secrets in the database.\n"
                "To generate a valid key, run this command in your terminal:\n"
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        # Try to load as Fernet key
        from cryptography.fernet import Fernet

        try:
            Fernet(v.encode())
        except Exception as e:
            raise ValueError(f"Invalid Fernet key: {e}") from e
        return v

    @model_validator(mode="after")
    def assemble_connections(self) -> "Settings":
        # Always construct DATABASE_URL from components to ensure consistency
        self.DATABASE_URL = (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
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

        # Interpolate PARTNER_AUTHORITY if it contains placeholder
        if "${PARTNER_TENANT_ID}" in self.PARTNER_AUTHORITY:
            self.PARTNER_AUTHORITY = self.PARTNER_AUTHORITY.replace(
                "${PARTNER_TENANT_ID}", self.PARTNER_TENANT_ID
            )
        # Fallback for PARTNER_AUTHORITY if still empty
        if not self.PARTNER_AUTHORITY:
            self.PARTNER_AUTHORITY = (
                f"https://login.microsoftonline.com/{self.PARTNER_TENANT_ID}"
            )

        # Construct REDIS_URL if not provided
        if not self.REDIS_URL:
            password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.REDIS_URL = f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

        return self

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


settings = Settings()
