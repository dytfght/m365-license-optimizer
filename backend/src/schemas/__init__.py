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
from .analytics import (
    AnalyticsMetricCreate,
    AnalyticsMetricFilter,
    AnalyticsMetricListResponse,
    AnalyticsMetricResponse,
    AnalyticsMetricUpdate,
    AnalyticsSnapshotCreate,
    AnalyticsSnapshotFilter,
    AnalyticsSnapshotListResponse,
    AnalyticsSnapshotResponse,
    AnalyticsSnapshotUpdate,
    AnalyticsSummaryResponse,
    DashboardKPIsResponse,
    KPIResponse,
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
    # Analytics
    "AnalyticsMetricCreate",
    "AnalyticsMetricResponse",
    "AnalyticsMetricUpdate",
    "AnalyticsMetricListResponse",
    "AnalyticsMetricFilter",
    "AnalyticsSnapshotCreate",
    "AnalyticsSnapshotResponse",
    "AnalyticsSnapshotUpdate",
    "AnalyticsSnapshotListResponse",
    "AnalyticsSnapshotFilter",
    "AnalyticsSummaryResponse",
    "DashboardKPIsResponse",
    "KPIResponse",
]
