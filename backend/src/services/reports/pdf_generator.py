"""
PDF Generator - Fixed version without Calibri fonts
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Image, SimpleDocTemplate, Spacer, Table, TableStyle

from src.services.i18n_service import i18n_service

logger = structlog.get_logger(__name__)


class PDFGenerator:
    def __init__(self):
        self.COLORS = {
            "primary": HexColor("#0078d4"),
            "secondary": HexColor("#40E0D0"),
            "success": colors.green,
            "danger": colors.red,
            "warning": colors.orange,
            "light_grey": HexColor("#f8f9fa"),
            "white": colors.white,
            "text": HexColor("#323130"),
        }
        # Use standard Helvetica fonts - no external fonts needed
        logger.debug("pdf_generator_initialized", fonts="Helvetica (standard)")

    def generate_executive_summary(self, data: Dict[str, Any], language: str = "en") -> bytes:
        """Generate complete executive summary PDF"""
        logger.info("generating_pdf_report", analysis_id=data.get("analysis_id"), language=language)

        # Set language for translations
        i18n_service.set_default_language(language)

        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=i18n_service.translate("report.title.pdf", language),
            author="M365 License Optimizer",
        )

        # Build content
        story = []

        # 1. Header section
        story.append(self._create_header(data, language))
        story.append(Spacer(1, 30))

        # 2. KPI section
        story.append(self._create_kpi_section(data, language))
        story.append(Spacer(1, 25))

        # 3. License distribution chart
        story.append(self._create_license_distribution_chart(data, language))
        story.append(Spacer(1, 25))

        # 4. Top recommendations
        story.append(self._create_recommendations_section(data, language))
        story.append(Spacer(1, 20))

        # 5. Department breakdown (if available)
        if data.get("departments"):
            story.append(self._create_departments_table(data, language))
            story.append(Spacer(1, 20))

        # 6. Footer
        story.append(self._create_footer(language))

        # Build PDF
        doc.build(story)

        pdf_content = buffer.getvalue()

        logger.info("pdf_generated_successfully", size_bytes=len(pdf_content))

        return pdf_content

    def _create_header(self, data: Dict[str, Any], language: str) -> Table:
        """Create header with logo, title and dates"""

        # LOG INFO: Vérifier les traductions
        logger.info("pdf_header_debug",
                   language=language,
                   title_key="report.title.pdf_summary",
                   title_result=i18n_service.translate("report.title.pdf_summary", language),
                   data_period_key="report.data_period",
                   data_period_result=i18n_service.translate("report.data_period", language))

        # Header layout: [Logo area, Title area]
        header_data = [
            [
                # Logo image (if provided) or fallback text
                Image(data.get("logo_path", "assets/default_logo.png"), width=2.5*cm, height=1.2*cm)
                if data.get("logo_path") or Path("assets/default_logo.png").exists()
                else "LOGO",
                data.get("title", i18n_service.translate("report.title.pdf_summary", language))
            ],
            [
                "",
                f"{i18n_service.translate('report.data_period', language)}: {data.get('period_start', '')} to {data.get('period_end', '')}",
            ],
            ["", f"{i18n_service.translate('report.generated_on', language)}: {i18n_service.format_date(datetime.now(), language, 'full')}"],
        ]

        header_table = Table(
            header_data,
            colWidths=[3 * cm, 14 * cm],
            rowHeights=[1.5 * cm, 0.8 * cm, 0.8 * cm],
        )

        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.COLORS["primary"]),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.COLORS["white"]),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (1, 0), (1, 0), 18),
                    ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (1, 1), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        return header_table

    def _create_kpi_section(self, data: Dict[str, Any], language: str) -> Table:
        """Create KPI tiles section"""

        kpis = data.get("kpis", {})

        # KPI data for 4 tiles
        kpi_data1 = [
            [
                i18n_service.translate("report.total_users", language),
                i18n_service.translate("report.total_licenses", language),
                i18n_service.translate("report.total_monthly_cost", language),
                i18n_service.translate("report.potential_annual_savings", language),
            ],
        ]

        kpi_data2 = [
            [
                f"{kpis.get('total_users', 0):,}",
                f"{kpis.get('total_licenses', 0) or sum(kpis.get('license_distribution', {}).values()):,}",
                f"${kpis.get('current_monthly_cost', 0):,.2f}",
                f"${kpis.get('annual_savings', 0):,.2f}",
            ],
        ]

        # Create KPI table
        kpi_table = Table(kpi_data1, colWidths=[4.25 * cm] * 4)
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.COLORS["light_grey"]),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.COLORS["text"]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        kpi_table2 = Table(kpi_data2, colWidths=[4.25 * cm] * 4)
        kpi_table2.setStyle(
            TableStyle(
                [
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.COLORS["text"]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 16),
                ]
            )
        )

        # Combine tables
        combined_data = [(kpi_table,), (kpi_table2,)]
        combined_table = Table(combined_data, colWidths=[17 * cm])

        return combined_table

    def _create_license_distribution_chart(self, data: Dict[str, Any], language: str):
        """Create license distribution chart with matplotlib"""

        # Generate chart image
        chart_image = self._create_donut_chart_matplotlib(data, language)

        if chart_image:
            try:
                # Use the generated chart image
                img = Image(io.BytesIO(chart_image), width=17*cm, height=7*cm)
                return img
            except Exception as e:
                logger.warning("chart_image_error", error=str(e))

        # Fallback to placeholder table if chart generation fails
        chart_table = Table(
            [[i18n_service.translate("report.license_distribution_chart", language)]],
            colWidths=[17 * cm],
            rowHeights=[7 * cm],
        )

        chart_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.COLORS["light_grey"]),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.COLORS["text"]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 14),
                ]
            )
        )

        return chart_table
    def _create_recommendations_section(self, data: Dict[str, Any], language: str) -> Table:
        """Create top recommendations table"""

        recommendations = data.get("top_recommendations", [])

        if not recommendations:
            recommendations_table = Table(
                [[i18n_service.translate("report.no_recommendations_available", language)]],
                colWidths=[17 * cm],
                rowHeights=[1.5 * cm],
            )
        else:
            # Header row
            header_row = [
                i18n_service.translate("report.from_to", language),
                i18n_service.translate("report.monthly_savings_per_user_short", language),
                i18n_service.translate("report.annual_savings_per_user_short", language),
                i18n_service.translate("report.user_count_short", language),
                i18n_service.translate("report.annual_savings_dept_short", language),
            ]

            # Data rows
            rows = [header_row]
            total_annual_savings = 0

            for rec in recommendations[:5]:  # Top 5
                row = [
                    f"{rec.get('from', '')} → {rec.get('to', '')}",
                    f"${rec.get('monthly_savings_per_user', 0):.2f}",
                    f"${rec.get('annual_savings_per_user', 0):.2f}",
                    f"{rec.get('user_count', 0)}",
                    f"${rec.get('total_annual_savings', 0):,.2f}",
                ]
                rows.append(row)
                total_annual_savings += rec.get('total_annual_savings', 0)

            # Summary row
            summary_row = [
                i18n_service.translate("report.total_savings", language),
                "",
                "",
                "",
                f"${total_annual_savings:,.2f}",
            ]
            rows.append(summary_row)

            recommendations_table = Table(rows, colWidths=[5 * cm, 3 * cm, 3.5 * cm, 2.5 * cm, 3 * cm])

            # Apply styles
            style = [
                ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), self.COLORS["white"]),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]

            # Header row style
            for i in range(1, len(rows)):
                style.append(("BACKGROUND", (0, i), (-1, i), self.COLORS["light_grey"]))

            # Total row style
            style.append(("BACKGROUND", (0, -1), (-1, -1), colors.yellow))
            style.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))

            recommendations_table.setStyle(TableStyle(style))

        return recommendations_table

    def _create_departments_table(self, data: Dict[str, Any], language: str) -> Table:
        """Create departments optimization table"""

        departments = data.get("departments", {})

        if not departments:
            no_data_table = Table(
                [[i18n_service.translate("report.no_department_data", language)]],
                colWidths=[17 * cm],
                rowHeights=[1.5 * cm],
            )
            return no_data_table

        # Header row
        header_row = [
            i18n_service.translate("report.department", language),
            i18n_service.translate("report.user_count", language),
            i18n_service.translate("report.current_monthly", language),
            i18n_service.translate("report.optimized_monthly", language),
            i18n_service.translate("report.annual_savings_dept_short", language),
        ]

        # Data rows
        rows = [header_row]
        total_users = 0
        total_current_monthly = 0
        total_optimized_monthly = 0
        total_annual_savings = 0

        for dept_name, dept_data in departments.items():
            if isinstance(dept_data, dict):
                users = dept_data.get("user_count", 0)
                current_monthly = dept_data.get("current_monthly_cost", 0)
                optimized_monthly = dept_data.get("optimized_monthly_cost", 0)
                savings = (current_monthly - optimized_monthly) * 12

                row = [
                    dept_name,
                    f"{users}",
                    f"${current_monthly:,.2f}",
                    f"${optimized_monthly:,.2f}",
                    f"${savings:,.2f}",
                ]
                rows.append(row)

                total_users += users
                total_current_monthly += current_monthly
                total_optimized_monthly += optimized_monthly
                total_annual_savings += savings

        # Total row
        total_row = [
            i18n_service.translate("report.total", language),
            f"{total_users}",
            f"${total_current_monthly:,.2f}",
            f"${total_optimized_monthly:,.2f}",
            f"${total_annual_savings:,.2f}",
        ]
        rows.append(total_row)

        departments_table = Table(rows, colWidths=[6 * cm, 2.5 * cm, 3 * cm, 3 * cm, 2.5 * cm])

        # Apply styles
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["primary"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.COLORS["white"]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]

        # Data row styles
        for i in range(1, len(rows)):
            style.append(("BACKGROUND", (0, i), (-1, i), self.COLORS["light_grey"]))

        # Total row style
        style.append(("BACKGROUND", (0, -1), (-1, -1), colors.yellow))
        style.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))

        departments_table.setStyle(TableStyle(style))

        return departments_table

    def _create_footer(self, language: str) -> Table:
        """Create footer with confidential notice"""

        footer_table = Table(
            [[i18n_service.translate("report.confidential_notice", language)]],
            colWidths=[17 * cm],
            rowHeights=[0.8 * cm],
        )

        footer_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.COLORS["light_grey"]),
                    ("TEXTCOLOR", (0, 0), (-1, -1), self.COLORS["text"]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )

        return footer_table

    def _create_donut_chart_matplotlib(self, data: Dict[str, Any], language: str) -> Optional[bytes]:
        """Create matplotlib donut chart - placeholder"""
        try:
            import matplotlib.pyplot as plt

            labels = ["Office 365 E3", "Microsoft 365 E3", "Office 365 E5", "Microsoft 365 E5", "Others"]
            sizes = [35, 25, 20, 15, 5]
            colors = ["#0078d4", "#40E0D0", "#5a5a5a", "#2c3e50", "#95a5a6"]

            fig, ax = plt.subplots(figsize=(8, 6))
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.0f%%",
                startangle=90,
                wedgeprops=dict(width=0.3, edgecolor="w"),
            )

            plt.setp(autotexts, size=10, weight="bold")
            plt.setp(texts, size=10)

            plt.title(i18n_service.translate("report.license_distribution", language), fontsize=14, fontweight="bold")

            buffer = io.BytesIO()
            plt.savefig(buffer, format="png", bbox_inches="tight", dpi=150, transparent=True)
            plt.close(fig)
            buffer.seek(0)

            return buffer.read()
        except ImportError:
            logger.warning("matplotlib_not_available", message="Matplotlib not installed, skipping chart generation")
            return None
