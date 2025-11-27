"""
Pydantic schemas package
"""
from .analysis import (
    AnalysisCreate,
    AnalysisDetailResponse,
    AnalysisList,
    AnalysisResponse,
    AnalysisSummary,
)
from .health import DetailedHealthCheck, HealthCheck, VersionResponse
from .recommendation import (
    ApplyRecommendationRequest,
    ApplyRecommendationResponse,
    RecommendationCreate,
    RecommendationList,
    RecommendationResponse,
)
from .tenant import TenantCreate, TenantList, TenantResponse, TenantUpdate
from .token import RefreshTokenRequest, RefreshTokenResponse, Token, TokenPayload
from .user import UserCreate, UserLogin, UserResponse, UserUpdate

__all__ = [
    # Health
    "HealthCheck",
    "DetailedHealthCheck",
    "VersionResponse",
    # Tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantList",
    # Token
    "Token",
    "TokenPayload",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    # User
    "UserLogin",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Analysis
    "AnalysisCreate",
    "AnalysisResponse",
    "AnalysisDetailResponse",
    "AnalysisSummary",
    "AnalysisList",
    # Recommendation
    "RecommendationCreate",
    "RecommendationResponse",
    "ApplyRecommendationRequest",
    "ApplyRecommendationResponse",
    "RecommendationList",
]
