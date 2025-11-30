"""
Database models for M365 License Optimizer
"""
from .addon_compatibility import AddonCompatibility
from .analysis import Analysis, AnalysisStatus
from .analytics import AnalyticsMetric, AnalyticsSnapshot, MetricType, SnapshotType
from .base import Base
from .microsoft_price import MicrosoftPrice
from .microsoft_product import MicrosoftProduct
from .recommendation import Recommendation, RecommendationStatus
from .report import Report
from .tenant import TenantAppRegistration, TenantClient
from .usage_metrics import UsageMetrics
from .user import AssignmentSource, LicenseAssignment, LicenseStatus, User

__all__ = [
    "Base",
    "TenantClient",
    "TenantAppRegistration",
    "User",
    "LicenseAssignment",
    "LicenseStatus",
    "AssignmentSource",
    "UsageMetrics",
    "MicrosoftProduct",
    "MicrosoftPrice",
    "AddonCompatibility",
    "Analysis",
    "AnalysisStatus",
    "Recommendation",
    "RecommendationStatus",
    "Report",
    "AnalyticsMetric",
    "AnalyticsSnapshot",
    "MetricType",
    "SnapshotType",
]
