"""
Database models for M365 License Optimizer
"""
from .base import Base
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
]
