"""
PDF Report Generator - Creates executive summary PDF reports
"""
import io
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend

import structlog

logger = structlog.get_logger(__name__)


class PDFGenerator:
    """Generate executive summary PDF reports with Microsoft design"""
    
    # Microsoft color palette
    COLORS = {
        'primary': colors.HexColor("#0078D4"),      # Microsoft blue
        'background': colors.HexColor("#F3F2F1"),  # Light gray
        'text': colors.HexColor("#323130"),        # Dark gray
        'text_secondary': colors.HexColor("#605E5C"),  # Medium gray
        'success': colors.HexColor("#107C10"),     # Green
        'warning': colors.HexColor("#FF8C00"),     # Orange
        'error': colors.HexColor("#D13438"),       # Red
        'white': colors.white,
        'black': colors.black,
    }
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for Microsoft design"""
        
        # Header title
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=self.COLORS['white'],
            spaceAfter=12,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        ))
        
        # Section headers
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=self.COLORS['primary'],
            spaceAfter=12,
            spaceBefore=18,
            fontName='Helvetica-Bold'
        ))
        
        # KPI values
        self.styles.add(ParagraphStyle(
            name='KPIValue',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=self.COLORS['primary'],
            spaceAfter=6,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        ))
        
        # KPI labels
        self.styles.add(ParagraphStyle(
            name='KPILabel',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.COLORS['text_secondary'],
            spaceAfter=0,
            alignment=1,  # Center
            fontName='Helvetica'
        ))
        
        # Recommendation text
        self.styles.add(ParagraphStyle(
            name='Recommendation',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.COLORS['text'],
            spaceAfter=8,
            leftIndent=20,
            bulletIndent=10,
            fontName='Helvetica'
        ))
        
        # Footer text
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.COLORS['text_secondary'],
            spaceAfter=6,
            alignment=1,  # Center
            fontName='Helvetica'
        ))

    def generate_executive_summary(self, data: Dict[str, Any]) -> bytes:
        """Generate complete executive summary PDF"""
        
        logger.info("generating_pdf_report", analysis_id=data.get("analysis_id"))
        
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title="Microsoft 365 License Optimization Report",
            author="M365 License Optimizer"
        )
        
        # Build content
        story = []
        
        # 1. Header section
        story.append(self._create_header(data))
        story.append(Spacer(1, 30))
        
        # 2. KPI section
        story.append(self._create_kpi_section(data))
        story.append(Spacer(1, 25))
        
        # 3. License distribution chart
        story.append(self._create_license_distribution_chart(data))
        story.append(Spacer(1, 25))
        
        # 4. Top recommendations
        story.append(self._create_recommendations_section(data))
        story.append(Spacer(1, 20))
        
        # 5. Department breakdown (if available)
        if data.get("departments"):
            story.append(self._create_departments_table(data))
            story.append(Spacer(1, 20))
        
        # 6. Footer
        story.append(self._create_footer())
        
        # Build PDF
        doc.build(story)
        
        pdf_content = buffer.getvalue()
        
        logger.info("pdf_generated_successfully", size_bytes=len(pdf_content))
        
        return pdf_content

    def _create_header(self, data: Dict[str, Any]) -> Table:
        """Create header with logo, title and dates"""
        
        # Header layout: [Logo area, Title area]
        header_data = [
            ["LOGO", data.get("title", "Analyse d'optimisation Microsoft 365")],
            ["", f"Données du {data.get('period_start', '')} au {data.get('period_end', '')}"],
            ["", f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"]
        ]
        
        header_table = Table(
            header_data, 
            colWidths=[3*cm, 14*cm],
            rowHeights=[1.5*cm, 0.8*cm, 0.8*cm]
        )
        
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLORS['white']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (1, 0), (1, 0), 18),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        return header_table

    def _create_kpi_section(self, data: Dict[str, Any]) -> Table:
        """Create KPI tiles section"""
        
        kpis = data.get("kpis", {})
        
        # KPI data for 4 tiles
        kpi_data = [
            [
                Paragraph("Coût actuel mensuel", self.styles['KPILabel']),
                Paragraph(f"{kpis.get('current_monthly_cost', 0):,.0f} €", self.styles['KPIValue']),
                ""
            ],
            [
                Paragraph("Économie mensuelle", self.styles['KPILabel']),
                Paragraph(f"{kpis.get('monthly_savings', 0):,.0f} €", self.styles['KPIValue']),
                Paragraph(f"({kpis.get('savings_percentage', 0):.0f}%)", self.styles['KPILabel'])
            ],
            [
                Paragraph("Économie annuelle", self.styles['KPILabel']),
                Paragraph(f"{kpis.get('annual_savings', 0):,.0f} €", self.styles['KPIValue']),
                ""
            ],
            [
                Paragraph("Utilisateurs analysés", self.styles['KPILabel']),
                Paragraph(f"{kpis.get('total_users', 0)}", self.styles['KPIValue']),
                ""
            ]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
        
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['background']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLORS['text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('HEIGHT', (0, 0), (-1, -1), 3*cm),
        ]))
        
        return kpi_table

    def _create_license_distribution_chart(self, data: Dict[str, Any]) -> Table:
        """Create license distribution donut chart"""
        
        license_data = data.get("license_distribution", [])
        if not license_data:
            return Table([["Aucune donnée de licence disponible"]], colWidths=[19*cm])
        
        # Create chart data
        chart_data = []
        labels = []
        colors_list = []
        
        # Microsoft color palette for charts
        ms_colors = [
            "#0078D4",  # Blue
            "#00BCF2",  # Cyan
            "#8764B8",  # Purple
            "#FF8C00",  # Orange
            "#107C10",  # Green
            "#E3008C",  # Pink
        ]
        
        for i, item in enumerate(license_data[:6]):  # Max 6 items
            chart_data.append(item.get("user_count", 0))
            labels.append(f"{item.get('license_name', 'Unknown')} ({item.get('percentage', 0)}%)")
            colors_list.append(ms_colors[i % len(ms_colors)])
        
        # Create pie chart
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 50
        pie.y = 50
        pie.width = 100
        pie.height = 100
        pie.data = chart_data
        pie.labels = labels
        pie.slices.strokeWidth = 0
        
        # Set colors
        for i, color in enumerate(colors_list):
            pie.slices[i].fillColor = colors.HexColor(color)
        
        drawing.add(pie)
        
        # Create chart section
        chart_section_data = [
            [Paragraph("Répartition actuelle des licences par SKU", self.styles['SectionHeader'])],
            [drawing]
        ]
        
        chart_table = Table(chart_section_data, colWidths=[19*cm])
        chart_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return chart_table

    def _create_recommendations_section(self, data: Dict[str, Any]) -> Table:
        """Create top recommendations section"""
        
        recommendations = data.get("top_recommendations", [])
        
        if not recommendations:
            return Table([["Aucune recommandation disponible"]], colWidths=[19*cm])
        
        # Section header
        header = Paragraph("Actions prioritaires", self.styles['SectionHeader'])
        
        # Recommendations list
        rec_data = []
        for i, rec in enumerate(recommendations[:3], 1):  # Top 3
            rec_text = (
                f"{i}. {rec.get('count', 0)} utilisateurs {rec.get('from_license', '')} → "
                f"{rec.get('to_license', '')} : économie {rec.get('annual_savings', 0):,.0f}€/an"
            )
            rec_para = Paragraph(f"✓ {rec_text}", self.styles['Recommendation'])
            rec_data.append([rec_para])
        
        # Combine header and recommendations
        section_data = [[header]] + rec_data
        
        section_table = Table(section_data, colWidths=[19*cm])
        section_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return section_table

    def _create_departments_table(self, data: Dict[str, Any]) -> Table:
        """Create departments breakdown table"""
        
        departments = data.get("departments", [])
        
        if not departments:
            return Table([["Aucune donnée de département disponible"]], colWidths=[19*cm])
        
        # Table header
        header_data = [
            ["Département", "Utilisateurs", "Coût actuel", "Coût cible", "Économie annuelle"]
        ]
        
        # Table content (top 5 departments)
        table_data = header_data.copy()
        
        for dept in departments[:5]:  # Top 5
            row = [
                dept.get("name", ""),
                f"{dept.get('user_count', 0)}",
                f"{dept.get('current_cost', 0):,.0f}€",
                f"{dept.get('target_cost', 0):,.0f}€",
                f"{dept.get('annual_savings', 0):,.0f}€"
            ]
            table_data.append(row)
        
        dept_table = Table(table_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm, 5*cm])
        
        dept_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['background']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F8F8")]),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return dept_table

    def _create_footer(self) -> Table:
        """Create footer section"""
        
        footer_text = [
            "Généré par M365 License Optimizer v1.0 - Confidentiel",
            "Ce rapport contient des recommandations basées sur l'usage réel. Validation métier requise avant application.",
            "Page 1/1"
        ]
        
        footer_data = [[Paragraph(text, self.styles['Footer'])] for text in footer_text]
        
        footer_table = Table(footer_data, colWidths=[19*cm])
        
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['background']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.COLORS['text_secondary']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('HEIGHT', (0, 0), (-1, -1), 2*cm),
        ]))
        
        return footer_table

    def _create_donut_chart_matplotlib(self, data: Dict[str, Any]) -> bytes:
        """Create donut chart using matplotlib (alternative implementation)"""
        
        license_data = data.get("license_distribution", [])
        if not license_data:
            return b""
        
        # Prepare data
        labels = [item.get("license_name", f"License {i}") for i, item in enumerate(license_data)]
        sizes = [item.get("user_count", 0) for item in license_data]
        colors = ["#0078D4", "#00BCF2", "#8764B8", "#FF8C00", "#107C10", "#E3008C"]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        
        # Create donut chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors[:len(sizes)],
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops=dict(width=0.5)  # Donut effect
        )
        
        # Style the chart
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        for text in texts:
            text.set_fontsize(9)
        
        # Title
        ax.set_title(
            "Répartition actuelle des licences par SKU",
            fontsize=12,
            fontweight='bold',
            color='#0078D4'
        )
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        
        plt.close(fig)  # Close to free memory
        
        return img_buffer.getvalue()