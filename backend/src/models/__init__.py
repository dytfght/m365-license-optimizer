"""
Database models for M365 License Optimizer
"""
from .base import Base
from .tenant import TenantClient, TenantAppRegistration
from .user import User, LicenseAssignment, LicenseStatus, AssignmentSource

__all__ = [
    "Base",
    "TenantClient",
    "TenantAppRegistration",
    "User",
    "LicenseAssignment",
    "LicenseStatus",
    "AssignmentSource",
]
