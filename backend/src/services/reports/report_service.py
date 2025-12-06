"""
Report Service - Main service for generating PDF and Excel reports
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.analysis import Analysis
from ...models.report import Report
from ...repositories.analysis_repository import AnalysisRepository
from ...repositories.recommendation_repository import RecommendationRepository
from ...services.i18n_service import I18nService
from .chart_generator import ChartGenerator
from .excel_generator_simple import ExcelGenerator
from .pdf_generator import PDFGenerator

logger = structlog.get_logger(__name__)


class ReportService:
    """Main service for generating PDF and Excel reports"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.pdf_generator = PDFGenerator()
        self.excel_generator = ExcelGenerator()
        self.chart_generator = ChartGenerator()
        self.analysis_repo = AnalysisRepository(session)
        self.recommendation_repo = RecommendationRepository(session)
        self.i18n_service = I18nService()

    async def generate_pdf_report(
        self,
        analysis_id: UUID,
        generated_by: str,
        language: Optional[str] = None,
        tenant_logo_path: Optional[str] = None,
    ) -> Report:
        """Generate executive summary PDF report"""

        lang = language or self.i18n_service.default_language
        self.i18n_service.set_default_language(lang)

        logger.info(
            "generating_pdf_report",
            analysis_id=str(analysis_id),
            generated_by=generated_by,
            language=lang,
        )

        # Get complete analysis with all data
        analysis = await self._get_analysis_with_data(analysis_id)

        # Prepare report data with localized content
        report_data = await self._prepare_localized_report_data(analysis, lang)

        # Generate PDF (synchronous operation)
        pdf_content = self.pdf_generator.generate_executive_summary(report_data, language=lang)

        # Save file
        file_name = f"m365_optimization_{analysis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = await self._save_report_file(
            content=pdf_content, file_name=file_name, mime_type="application/pdf"
        )

        # Create database entry
        report = Report(
            analysis_id=analysis_id,
            tenant_client_id=analysis.tenant_client_id,
            report_type="PDF",
            file_name=file_name,
            file_path=file_path,
            file_size_bytes=len(pdf_content),
            mime_type="application/pdf",
            report_metadata={
                **report_data.get("metadata", {}),
                "language": lang,
            },
            generated_by=generated_by,
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),  # 90 days TTL
        )

        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)

        logger.info(
            "pdf_report_generated_successfully",
            report_id=str(report.id),
            analysis_id=str(analysis_id),
            language=lang,
            file_size=len(pdf_content),
        )

        return report

    async def generate_excel_report(
        self, analysis_id: UUID, generated_by: str, language: Optional[str] = None
    ) -> Report:
        """Generate detailed Excel report"""

        lang = language or self.i18n_service.default_language
        self.i18n_service.set_default_language(lang)

        logger.info(
            "generating_excel_report",
            analysis_id=str(analysis_id),
            generated_by=generated_by,
            language=lang,
        )

        # Get complete analysis with all data
        analysis = await self._get_analysis_with_data(analysis_id)

        # Prepare report data with localized content
        report_data = await self._prepare_localized_report_data(analysis, lang)

        # Generate Excel (synchronous operation)
        excel_content = await self.excel_generator.generate_detailed_excel(report_data, language=lang)

        # Save file
        file_name = f"m365_optimization_detailed_{analysis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = await self._save_report_file(
            content=excel_content,
            file_name=file_name,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Create database entry
        report = Report(
            analysis_id=analysis_id,
            tenant_client_id=analysis.tenant_client_id,
            report_type="EXCEL",
            file_name=file_name,
            file_path=file_path,
            file_size_bytes=len(excel_content),
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            report_metadata={
                **report_data.get("metadata", {}),
                "language": lang,
            },
            generated_by=generated_by,
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),  # 90 days TTL
        )

        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)

        logger.info(
            "excel_report_generated_successfully",
            report_id=str(report.id),
            analysis_id=str(analysis_id),
            language=lang,
            file_size=len(excel_content),
        )

        return report

    async def get_report_by_id(self, report_id: UUID) -> Optional[Report]:
        """Get report by ID (excluding expired reports)"""
        from datetime import timezone

        result = await self.session.execute(
            select(Report).where(
                Report.id == report_id,
                (Report.expires_at.is_(None))
                | (Report.expires_at > datetime.now(timezone.utc)),
            )
        )
        return result.scalar_one_or_none()

    async def get_reports_by_analysis(self, analysis_id: UUID) -> List[Report]:
        """Get all reports for an analysis"""

        result = await self.session.execute(
            select(Report)
            .where(Report.analysis_id == analysis_id)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_reports_by_tenant(self, tenant_id: UUID) -> List[Report]:
        """Get all reports for a tenant"""

        result = await self.session.execute(
            select(Report)
            .where(Report.tenant_client_id == tenant_id)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_report(self, report_id: UUID) -> bool:
        """Soft delete a report"""

        report = await self.get_report_by_id(report_id)
        if not report:
            return False

        # Soft delete by updating expires_at
        report.expires_at = datetime.now(timezone.utc)
        await self.session.commit()

        logger.info("report_deleted", report_id=str(report_id))
        return True

    async def cleanup_expired_reports(self) -> int:
        """Clean up reports that have expired"""

        now = datetime.now(timezone.utc)

        result = await self.session.execute(
            select(Report).where(Report.expires_at < now)
        )
        expired_reports = list(result.scalars().all())

        deleted_count = 0
        for report in expired_reports:
            try:
                # Delete physical file
                file_path = Path(report.file_path)
                if file_path.exists():
                    file_path.unlink()

                # Delete database entry
                await self.session.delete(report)
                deleted_count += 1

                logger.info(
                    "expired_report_cleaned",
                    report_id=str(report.id),
                    file_path=str(file_path),
                )

            except Exception as e:
                logger.error(
                    "failed_to_cleanup_report", report_id=str(report.id), error=str(e)
                )

        if deleted_count > 0:
            await self.session.commit()

        logger.info("cleanup_completed", deleted_count=deleted_count)
        return deleted_count

    # Private helper methods

    async def _get_analysis_with_data(self, analysis_id: UUID) -> Analysis:
        """Get analysis with all related data"""

        analysis = await self.analysis_repo.get_by_id_with_recommendations(analysis_id)

        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        return analysis

    async def _prepare_report_data(self, analysis: Analysis) -> Dict[str, Any]:
        """Prepare data for report generation"""

        # Extract data from analysis
        summary = analysis.summary or {}

        # Prepare KPIs
        kpis = {
            "current_monthly_cost": summary.get("total_current_cost", 0),
            "target_monthly_cost": summary.get("total_optimized_cost", 0),
            "monthly_savings": summary.get("potential_savings_monthly", 0),
            "annual_savings": summary.get("potential_savings_annual", 0),
            "savings_percentage": self._calculate_savings_percentage(summary),
            "total_users": summary.get("total_users", 0),
        }

        # License distribution
        license_distribution = self._prepare_license_distribution(summary)

        # Top recommendations
        top_recommendations = self._prepare_top_recommendations(
            analysis.recommendations
        )

        # Departments breakdown
        departments = self._prepare_departments_breakdown(analysis.recommendations)

        # Tenant info - avoid accessing unloaded relationships
        tenant_name = (
            "Tenant"  # Valeur par défaut, on pourrait chercher le tenant si nécessaire
        )

        tenant_info = {
            "name": tenant_name,
            "period_start": analysis.analysis_date.strftime("%d/%m/%Y")
            if analysis.analysis_date
            else datetime.now(timezone.utc).strftime("%d/%m/%Y"),
            "period_end": (analysis.analysis_date + timedelta(days=28)).strftime(
                "%d/%m/%Y"
            )
            if analysis.analysis_date
            else datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        }

        return {
            "analysis_id": str(analysis.id),
            "tenant_id": str(analysis.tenant_client_id),
            "title": f"Analyse d'optimisation Microsoft 365 - {tenant_info['name']}",
            "period_start": tenant_info["period_start"],
            "period_end": tenant_info["period_end"],
            "kpis": kpis,
            "license_distribution": license_distribution,
            "top_recommendations": top_recommendations,
            "departments": departments,
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "report_version": "1.0",
                "tenant_name": tenant_info["name"],
            },
        }

    async def _prepare_localized_report_data(self, analysis: Analysis, language: str) -> Dict[str, Any]:
        """Prepare localized data for report generation"""

        # Get base report data
        report_data = await self._prepare_report_data(analysis)

        # Localize KPI titles
        kpis_localized = {
            "current_monthly_cost": {
                "value": report_data["kpis"]["current_monthly_cost"],
                "label": "",
            },
            "target_monthly_cost": {
                "value": report_data["kpis"]["target_monthly_cost"],
                "label": "",
            },
            "monthly_savings": {
                "value": report_data["kpis"]["monthly_savings"],
                "label": self.i18n_service.translate("report.potential_savings", language),
            },
            "annual_savings": {
                "value": report_data["kpis"]["annual_savings"],
                "label": "",
            },
            "savings_percentage": {
                "value": report_data["kpis"]["savings_percentage"],
                "label": "",
            },
            "total_users": {
                "value": report_data["kpis"]["total_users"],
                "label": self.i18n_service.translate("report.total_users", language),
            },
            "total_licenses": {
                "value": 0,  # This could be calculated if needed
                "label": self.i18n_service.translate("report.total_licenses", language),
            },
        }

        # Localize title
        title = self.i18n_service.translate("report.title.pdf", language)

        # Add localized sections
        sections = {
            "user_summary": self.i18n_service.translate("report.section.user_summary", language),
            "license_summary": self.i18n_service.translate("report.section.license_summary", language),
            "recommendations": self.i18n_service.translate("report.section.recommendations", language),
            "cost_analysis": self.i18n_service.translate("report.section.cost_analysis", language),
        }

        # IMPORTANT: Keep original KPI structure flat for backward compatibility
        # Add localized data separately without modifying original KPIs
        report_data["title"] = title
        report_data["language"] = language
        report_data["sections"] = sections
        
        # Add localized labels (but keep original KPI values flat)
        report_data["kpi_labels"] = {
            key: kpis_localized[key]["label"] for key in kpis_localized
        }

        return report_data

    def _calculate_savings_percentage(self, summary: Dict[str, Any]) -> float:
        """Calculate savings percentage"""
        current = summary.get("total_current_cost", 0)
        savings = summary.get("potential_savings_monthly", 0)

        if current > 0:
            return (savings / current) * 100
        return 0.0

    def _prepare_license_distribution(
        self, summary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Prepare license distribution data for charts"""

        # This would come from the analysis breakdown
        # For now, return mock data structure
        return summary.get(
            "license_breakdown",
            [
                {
                    "license_name": "Microsoft 365 E5",
                    "user_count": 50,
                    "percentage": 25.0,
                },
                {
                    "license_name": "Microsoft 365 E3",
                    "user_count": 80,
                    "percentage": 40.0,
                },
                {
                    "license_name": "Microsoft 365 Business Premium",
                    "user_count": 40,
                    "percentage": 20.0,
                },
                {
                    "license_name": "Microsoft 365 Business Standard",
                    "user_count": 20,
                    "percentage": 10.0,
                },
                {
                    "license_name": "Microsoft 365 Business Basic",
                    "user_count": 10,
                    "percentage": 5.0,
                },
            ],
        )

    def _prepare_top_recommendations(
        self, recommendations: List
    ) -> List[Dict[str, Any]]:
        """Prepare top recommendations sorted by savings"""

        # Group recommendations by type and calculate savings
        recommendation_groups = {}

        for rec in recommendations:
            rec_type = f"{rec.current_sku} → {rec.recommended_sku}"

            if rec_type not in recommendation_groups:
                recommendation_groups[rec_type] = {
                    "count": 0,
                    "from_license": rec.current_sku,
                    "to_license": rec.recommended_sku,
                    "monthly_savings": 0,
                    "annual_savings": 0,
                }

            recommendation_groups[rec_type]["count"] += 1
            recommendation_groups[rec_type]["monthly_savings"] += rec.savings_monthly
            recommendation_groups[rec_type]["annual_savings"] += (
                rec.savings_monthly * 12
            )

        # Sort by annual savings and return top 3
        sorted_recommendations = sorted(
            recommendation_groups.values(),
            key=lambda x: x["annual_savings"],
            reverse=True,
        )

        return sorted_recommendations[:3]

    def _prepare_departments_breakdown(
        self, recommendations: List
    ) -> List[Dict[str, Any]]:
        """Prepare departments breakdown"""

        # Group by department and calculate metrics
        department_groups: Dict[str, Dict[str, Any]] = {}

        for rec in recommendations:
            # Safely get user and department
            user = getattr(rec, "user", None)
            dept = getattr(user, "department", None) if user else None
            dept = dept if dept else "Non spécifié"

            if dept not in department_groups:
                department_groups[dept] = {
                    "name": dept,
                    "user_count": 0,
                    "current_cost": 0.0,
                    "target_cost": 0.0,
                    "annual_savings": 0.0,
                }

            department_groups[dept]["user_count"] += 1
            department_groups[dept]["current_cost"] += rec.current_cost_monthly
            department_groups[dept]["target_cost"] += rec.recommended_cost_monthly
            department_groups[dept]["annual_savings"] += rec.savings_monthly * 12

        # Sort by annual savings and return top 5
        sorted_departments = sorted(
            department_groups.values(), key=lambda x: x["annual_savings"], reverse=True
        )

        return sorted_departments[:5]

    async def _save_report_file(
        self, content: bytes, file_name: str, mime_type: str
    ) -> str:
        """Save report file to storage"""

        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        # Create subdirectory by date
        date_dir = reports_dir / datetime.now(timezone.utc).strftime("%Y/%m")
        date_dir.mkdir(parents=True, exist_ok=True)

        # Full file path
        file_path = date_dir / file_name

        # Write file
        try:
            with open(file_path, "wb") as f:
                f.write(content)

            logger.info(
                "report_file_saved", file_path=str(file_path), file_size=len(content)
            )

            return str(file_path)

        except Exception as e:
            logger.error(
                "failed_to_save_report_file", file_path=str(file_path), error=str(e)
            )
            raise RuntimeError(f"Failed to save report file: {e}")
