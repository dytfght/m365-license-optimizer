"""
Database models for M365 License Optimizer
"""
from .analysis import Analysis, AnalysisStatus
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
    "Analysis",
    "AnalysisStatus",
    "Recommendation",
    "RecommendationStatus",
    "Report",
]
