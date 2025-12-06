"""
GDPR Service for LOT 10: GDPR compliance operations
Handles consent management, data export, and right to be forgotten.
"""
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict
from uuid import UUID

import structlog
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.recommendation import Recommendation
from ..models.tenant import TenantClient
from ..models.usage_metrics import UsageMetrics
from ..models.user import LicenseAssignment, User

logger = structlog.get_logger(__name__)


class GdprService:
    """
    Service for GDPR compliance operations.
    Implements Articles 7 (consent), 17 (right to erasure), and 20 (data portability).
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize GDPR service.

        Args:
            db: Async database session
        """
        self.db = db

    # ============================================
    # Consent Management (GDPR Article 7)
    # ============================================

    async def record_consent(
        self, tenant_id: UUID, consent_given: bool = True
    ) -> TenantClient:
        """
        Record GDPR consent for a tenant.

        Args:
            tenant_id: Tenant UUID
            consent_given: Whether consent is given (default True)

        Returns:
            Updated TenantClient

        Raises:
            ValueError: If tenant not found
        """
        result = await self.db.execute(
            select(TenantClient).where(TenantClient.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            logger.warning("gdpr_consent_failed", tenant_id=str(tenant_id), reason="not_found")
            raise ValueError(f"Tenant {tenant_id} not found")

        tenant.gdpr_consent = consent_given
        tenant.gdpr_consent_date = datetime.now(timezone.utc) if consent_given else None

        await self.db.commit()
        await self.db.refresh(tenant)

        logger.info(
            "gdpr_consent_recorded",
            tenant_id=str(tenant_id),
            consent=consent_given,
        )

        return tenant

    async def check_consent(self, tenant_id: UUID) -> bool:
        """
        Check if a tenant has given GDPR consent.

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if consent has been given
        """
        result = await self.db.execute(
            select(TenantClient.gdpr_consent).where(TenantClient.id == tenant_id)
        )
        consent = result.scalar_one_or_none()
        return bool(consent)

    async def revoke_consent(self, tenant_id: UUID) -> TenantClient:
        """
        Revoke GDPR consent for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Updated TenantClient
        """
        return await self.record_consent(tenant_id, consent_given=False)

    # ============================================
    # Data Export / Portability (GDPR Article 20)
    # ============================================

    async def export_user_data(self, user_id: UUID) -> dict[str, Any]:
        """
        Export all personal data for a user (data portability).

        Args:
            user_id: User UUID

        Returns:
            Dictionary containing all user data in machine-readable format

        Raises:
            ValueError: If user not found
        """
        # Get user with all related data
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("gdpr_export_failed", user_id=str(user_id), reason="not_found")
            raise ValueError(f"User {user_id} not found")

        # Get license assignments
        licenses_result = await self.db.execute(
            select(LicenseAssignment).where(LicenseAssignment.user_id == user_id)
        )
        licenses = licenses_result.scalars().all()

        # Get usage metrics
        usage_result = await self.db.execute(
            select(UsageMetrics).where(UsageMetrics.user_id == user_id)
        )
        usage_metrics = usage_result.scalars().all()

        # Get recommendations
        recommendations_result = await self.db.execute(
            select(Recommendation).where(Recommendation.user_id == user_id)
        )
        recommendations = recommendations_result.scalars().all()

        export_data = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "export_type": "GDPR_ARTICLE_20_DATA_PORTABILITY",
            "user": {
                "id": str(user.id),
                "graph_id": user.graph_id,
                "user_principal_name": user.user_principal_name,
                "display_name": user.display_name,
                "department": user.department,
                "job_title": user.job_title,
                "office_location": user.office_location,
                "account_enabled": user.account_enabled,
                "member_of_groups": user.member_of_groups,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            },
            "license_assignments": [
                {
                    "sku_id": la.sku_id,
                    "assignment_date": la.assignment_date.isoformat() if la.assignment_date else None,
                    "status": la.status.value if la.status else None,
                    "source": la.source.value if la.source else None,
                }
                for la in licenses
            ],
            "usage_metrics": [

                {
                    "period": um.period,
                    "report_date": um.report_date.isoformat() if um.report_date else None,
                    "last_seen": um.last_seen_date.isoformat() if um.last_seen_date else None,
                    "storage_used": um.storage_used_bytes,
                    "email_activity": um.email_activity,
                    "teams_activity": um.teams_activity,
                    "onedrive_activity": um.onedrive_activity,
                    "sharepoint_activity": um.sharepoint_activity,
                }
                for um in usage_metrics
            ],
            "recommendations": [
                {
                    "id": str(r.id),
                    "status": r.status.value if r.status else None,
                    "current_sku": r.current_sku,
                    "recommended_sku": r.recommended_sku,
                    "savings_monthly": float(r.savings_monthly),
                    "reason": r.reason,
                }
                for r in recommendations
            ],
        }

        logger.info(
            "gdpr_data_exported",
            user_id=str(user_id),
            licenses_count=len(licenses),
            usage_count=len(usage_metrics),
        )

        return export_data

    async def export_tenant_data(self, tenant_id: UUID) -> dict[str, Any]:
        """
        Export all data for a tenant (for GDPR compliance).

        Args:
            tenant_id: Tenant UUID

        Returns:
            Dictionary containing all tenant data
        """
        result = await self.db.execute(
            select(TenantClient).where(TenantClient.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()

        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Get all users for this tenant
        users_result = await self.db.execute(
            select(User).where(User.tenant_client_id == tenant_id)
        )
        users = users_result.scalars().all()

        # Export each user's data
        users_data = []
        for user in users:
            try:
                # Cast to UUID explicitly to satisfy MyPy
                uid = UUID(str(user.id))
                user_data = await self.export_user_data(uid)
                users_data.append(user_data)
            except ValueError:
                continue

        return {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "export_type": "GDPR_TENANT_FULL_EXPORT",
            "tenant": {
                "id": str(tenant.id),
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "country": tenant.country,
                "gdpr_consent": tenant.gdpr_consent if hasattr(tenant, 'gdpr_consent') else None,
                "gdpr_consent_date": tenant.gdpr_consent_date.isoformat() if hasattr(tenant, 'gdpr_consent_date') and tenant.gdpr_consent_date else None,
            },
            "users": users_data,
            "total_users": len(users_data),
        }

    # ============================================
    # Right to Erasure (GDPR Article 17)
    # ============================================

    async def delete_user_data(
        self, user_id: UUID, anonymize: bool = False
    ) -> dict[str, Any]:
        """
        Delete or anonymize all personal data for a user.

        Args:
            user_id: User UUID
            anonymize: If True, anonymize instead of delete

        Returns:
            Summary of deleted/anonymized data

        Raises:
            ValueError: If user not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"User {user_id} not found")

        summary: Dict[str, Any] = {
            "user_id": str(user_id),
            "action": "anonymized" if anonymize else "deleted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_affected": {},
        }

        if anonymize:
            # Anonymize user data
            user.user_principal_name = f"anonymized_{user.id}@deleted.local"
            user.display_name = "Anonymized User"
            user.department = None
            user.job_title = None
            user.office_location = None
            user.member_of_groups = []
            user.password_hash = None

            summary["data_affected"]["user"] = "anonymized"

            # Delete related data
            await self.db.execute(
                delete(UsageMetrics).where(UsageMetrics.user_id == user_id)
            )
            summary["data_affected"]["usage_metrics"] = "deleted"

            await self.db.commit()
        else:
            # Full deletion - cascade will handle related records
            await self.db.delete(user)
            await self.db.commit()
            summary["data_affected"]["user"] = "deleted"
            summary["data_affected"]["related_records"] = "cascade_deleted"

        logger.info(
            "gdpr_user_data_erased",
            user_id=str(user_id),
            action=summary["action"],
        )

        return summary

    # ============================================
    # GDPR Registry (Article 30)
    # ============================================

    async def generate_registry_pdf(self) -> bytes:
        """
        Generate a PDF of the GDPR processing activities registry.

        Returns:
            PDF content as bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=30,
        )

        story = []

        # Title
        story.append(Paragraph("GDPR Processing Activities Registry", title_style))
        story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Processing activities table
        data = [
            ["Processing Activity", "Purpose", "Legal Basis", "Data Categories", "Retention"],
            ["User Authentication", "Access control", "Legitimate interest", "Email, password hash", "Account lifetime"],
            ["License Analysis", "Cost optimization", "Contract performance", "License assignments, usage", "90 days"],
            ["Usage Metrics", "Service optimization", "Legitimate interest", "Activity data", "90 days"],
            ["Audit Logging", "Security & compliance", "Legal obligation", "Request logs, IP", "90 days"],
            ["Recommendations", "Cost reduction", "Contract performance", "User assignments", "Analysis lifetime"],
        ]

        table = Table(data, colWidths=[120, 100, 100, 100, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        story.append(table)
        story.append(Spacer(1, 30))

        # Data Subject Rights
        story.append(Paragraph("Data Subject Rights Implementation", styles["Heading2"]))
        rights_data = [
            ["Right", "Implementation", "Endpoint"],
            ["Access (Art. 15)", "Export user data", "GET /gdpr/export/{user_id}"],
            ["Rectification (Art. 16)", "User profile update", "PUT /users/{id}"],
            ["Erasure (Art. 17)", "Delete/anonymize data", "DELETE /gdpr/delete/{user_id}"],
            ["Portability (Art. 20)", "JSON export", "GET /gdpr/export/{user_id}"],
            ["Consent (Art. 7)", "Record consent", "POST /gdpr/consent/{tenant_id}"],
        ]

        rights_table = Table(rights_data, colWidths=[120, 180, 180])
        rights_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 1), (-1, -1), colors.lightblue),
        ]))

        story.append(rights_table)

        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()

        logger.info("gdpr_registry_generated", size_bytes=len(pdf_content))

        return pdf_content
