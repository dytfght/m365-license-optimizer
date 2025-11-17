"""
Application configuration using Pydantic Settings
"""
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    APP_NAME: str = "M365 License Optimizer"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # Azure AD (Partner Authentication)
    AZURE_AD_TENANT_ID: str
    AZURE_AD_CLIENT_ID: str
    AZURE_AD_CLIENT_SECRET: str
    AZURE_AD_AUTHORITY: str = Field(default="")
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Microsoft Graph
    GRAPH_API_BASE_URL: str = "https://graph.microsoft.com/v1.0"
    GRAPH_API_SCOPES: str = "https://graph.microsoft.com/.default"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.AZURE_AD_AUTHORITY:
            self.AZURE_AD_AUTHORITY = f"https://login.microsoftonline.com/{self.AZURE_AD_TENANT_ID}"


settings = Settings()
