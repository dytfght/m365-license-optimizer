# LOT 7 - IMPLEMENTATION GUIDE
# Rapports PDF & Excel - License Optimization System

## 📋 Vue d'ensemble

**Objectif**: Implémenter la génération de rapports PDF exécutifs et Excel détaillés pour les analyses d'optimisation de licences Microsoft 365.

**Durée estimée**: 4 jours  
**Dépendances**: Lot 6 (Analysis system)  
**Complexité**: Moyenne  

## 🎯 Spécifications fonctionnelles

### 12.1 Rapport PDF Executive Summary (1 page)
- **Format**: A4 portrait, marges 2cm, police Segoe UI
- **Structure complète avec 6 sections** (voir détails ci-dessous)
- **Design**: Palette de couleurs Microsoft (#0078D4, #F3F2F1, etc.)
- **Contenu dynamique**: KPIs, graphiques, tableaux générés à partir des données d'analyse

### 12.2 Fichier Excel détaillé (3 feuilles)
- **Format**: XLSX (Excel 2016+)
- **Feuilles**: Synthèse, Recommandations détaillées, Données brutes
- **18 colonnes** avec formatage conditionnel et filtres
- **Formatage**: Couleurs, monétaire, dates, listes déroulantes

## 🏗️ Architecture technique

### Stack technique recommandée
- **PDF**: ReportLab + matplotlib (graphiques) + PIL (images)
- **Excel**: openpyxl (XLSX generation) + pandas (data manipulation)
- **Templates**: Jinja2 (optionnel pour complexité avancée)
- **Cache**: Redis pour stockage temporaire des rapports générés

### Structure des services
```
src/
├── services/
│   ├── report_service.py          # Service principal
│   ├── pdf_generator.py           # Génération PDF
│   ├── excel_generator.py         # Génération Excel
│   └── chart_generator.py         # Graphiques (donut, barres)
├── templates/                     # Templates optionnels
│   ├── report_pdf_template.html   # Si utilisation HTML→PDF
│   └── assets/
│       └── microsoft_colors.json  # Palette de couleurs
└── utils/
    ├── formatters.py              # Formatage monétaire, dates
    └── validators.py              # Validation des données
```

## 📊 Spécifications détaillées

### Rapport PDF - Structure complète

#### 1. En-tête (3cm, fond bleu Microsoft #0078D4)
- Logo tenant client (150×50px, gauche)
- Titre: "Analyse d'optimisation Microsoft 365" (blanc, 18pt, gras)
- Période: "Données du {date_debut} au {date_fin}" (blanc, 10pt)
- Date de génération: "Rapport généré le {date} à {heure}" (blanc, 10pt)

#### 2. Bloc KPIs principaux (4 tuiles, 5cm hauteur)
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Coût actuel │ Économie    │ Économie    │ Utilisateurs│
│ mensuel     │ mensuelle   │ annuelle    │ analysés    │
│             │             │             │             │
│ 15 420 €    │ 3 850 €     │ 46 200 €    │ 247         │
│             │ (-25%)      │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
```
- Fond: #F3F2F1, bordure 1px grise
- Valeurs: 24pt gras, couleur #0078D4
- Étiquettes: 12pt, couleur #605E5C

#### 3. Graphique en donut (8cm, centré)
- Titre: "Répartition actuelle des licences par SKU"
- Donut chart avec légende à droite
- Données: E5, E3, Business Premium, Business Standard, Business Basic, Autres
- Couleurs: Palette Microsoft (bleu, cyan, violet, orange, vert)

#### 4. Top 3 recommandations (5cm)
- Titre: "Actions prioritaires" (14pt gras)
- 3 bullet points numérotés avec icônes ✓ (coche verte)
- Exemples:
  1. "{nombre} utilisateurs E5 → E3 : économie {montant}€/an"
  2. "{nombre} comptes inactifs à désaffecter : économie {montant}€/an"
  3. "{nombre} licences Business Premium → Standard : économie {montant}€/an"

#### 5. Tableau par département (6cm, si disponible)
- Colonnes: Département | Utilisateurs | Coût actuel | Coût cible | Économie annuelle
- Max 5 départements (triés par économie décroissante)
- Style: Lignes alternées (gris clair/blanc)

#### 6. Footer (2cm, fond gris #F3F2F1)
- "Généré par M365 License Optimizer v1.0 - Confidentiel"
- "Ce rapport contient des recommandations basées sur l'usage réel. Validation métier requise avant application."
- "Page 1/1"

### Fichier Excel - Structure détaillée

#### Feuille 1: "Synthèse" (lecture seule)
- A1:B10: Résumé global (mêmes données que PDF KPIs)
- D1:H6: Tableau croisé dynamique suggestions par type
- A12:E25: Graphique en barres économies par département

#### Feuille 2: "Recommandations détaillées" (18 colonnes)

| Colonne | Description | Format |
|---------|-------------|--------|
| A | UserPrincipalName | Email, largeur 30 |
| B | DisplayName | Texte, largeur 25 |
| C | Department | Texte, largeur 20 |
| D | JobTitle | Texte, largeur 25 |
| E | CurrentLicense | Texte, largeur 30 |
| F | CurrentMonthlyCost | Monétaire 0.00€, largeur 15 |
| G | RecommendedLicense | Texte, largeur 30 |
| H | RecommendedMonthlyCost | Monétaire 0.00€, largeur 18 |
| I | MonthlySavings | Monétaire 0.00€, fond vert si >0, largeur 15 |
| J | AnnualSavings | Monétaire 0.00€, fond vert si >0, largeur 15 |
| K | ExchangeUsageLevel | Liste: Faible/Moyen/Élevé/Aucun, largeur 18 |
| L | OneDriveUsageGB | Nombre 0.00, largeur 18 |
| M | TeamsActivity | Liste: Faible/Moyen/Élevé/Aucun, largeur 15 |
| N | OfficeDesktopRequired | Booléen: Oui/Non, largeur 20 |
| O | LastActivityDate | Date JJ/MM/AAAA, largeur 18 |
| P | InactivityDays | Entier, fond rouge si >90, largeur 15 |
| Q | RecommendationStatus | Liste: Proposé/Validé/Rejeté/Sensible, largeur 22 |
| R | RecommendationReason | Texte multiligne, largeur 40 |

**Formatage conditionnel:**
- Colonne I (MonthlySavings): Fond vert dégradé selon montant
- Colonne P (InactivityDays): Fond rouge si >90 jours

#### Feuille 3: "Données brutes" (optionnelle)
- Export complet des données d'analyse
- Toutes les métriques brutes pour analyse approfondie

## 🔧 Implémentation technique

### 1. Modèles de données

```python
# models/report.py
from datetime import datetime
from uuid import UUID
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

class Report(Base):
    """Rapport généré (PDF ou Excel)"""
    __tablename__ = "reports"
    __table_args__ = {"schema": "optimizer"}
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    analysis_id = Column(PGUUID(as_uuid=True), ForeignKey("optimizer.analyses.id"), nullable=False)
    tenant_client_id = Column(PGUUID(as_uuid=True), ForeignKey("optimizer.tenant_clients.id"), nullable=False)
    
    report_type = Column(String(10), nullable=False)  # "PDF" ou "EXCEL"
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    mime_type = Column(String(100), nullable=False)
    
    # Métadonnées du rapport
    metadata = Column(JSONB, default=dict)  # KPIs, stats, etc.
    generated_by = Column(String(255), nullable=False)  # User email
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # TTL pour cleanup
    
    # Relations
    analysis = relationship("Analysis", back_populates="reports")
    tenant = relationship("TenantClient", back_populates="reports")
```

### 2. Service principal

```python
# services/report_service.py
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.report import Report
from ..models.analysis import Analysis
from ..models.tenant import TenantClient
from .pdf_generator import PDFGenerator
from .excel_generator import ExcelGenerator
from .chart_generator import ChartGenerator

logger = structlog.get_logger(__name__)

class ReportService:
    """Service principal pour génération de rapports"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.pdf_generator = PDFGenerator()
        self.excel_generator = ExcelGenerator()
        self.chart_generator = ChartGenerator()
        
    async def generate_pdf_report(
        self, 
        analysis_id: UUID, 
        generated_by: str,
        tenant_logo_path: Optional[str] = None
    ) -> Report:
        """Générer un rapport PDF exécutif"""
        
        # Récupérer l'analyse complète
        analysis = await self._get_analysis_with_data(analysis_id)
        
        # Préparer les données
        report_data = await self._prepare_pdf_data(analysis, tenant_logo_path)
        
        # Générer le PDF
        pdf_content = await self.pdf_generator.generate_executive_summary(report_data)
        
        # Sauvegarder le fichier
        file_path = await self._save_report_file(
            content=pdf_content,
            file_name=f"m365_optimization_{analysis.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime_type="application/pdf"
        )
        
        # Créer l'entrée en base
        report = Report(
            analysis_id=analysis_id,
            tenant_client_id=analysis.tenant_client_id,
            report_type="PDF",
            file_name=Path(file_path).name,
            file_path=file_path,
            file_size_bytes=len(pdf_content),
            mime_type="application/pdf",
            metadata=report_data.get("metadata", {}),
            generated_by=generated_by,
            expires_at=datetime.utcnow() + timedelta(days=90)  # 90 jours TTL
        )
        
        self.session.add(report)
        await self.session.commit()
        
        logger.info(
            "pdf_report_generated",
            report_id=str(report.id),
            analysis_id=str(analysis_id),
            file_size=len(pdf_content)
        )
        
        return report
```

### 3. Génération PDF

```python
# services/pdf_generator.py
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
import matplotlib.pyplot as plt
import io

class PDFGenerator:
    """Génération de rapports PDF exécutifs"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Configurer les styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=colors.white,
            spaceAfter=12,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='KPIValue',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor("#0078D4"),
            spaceAfter=6,
            alignment=1  # Center
        ))
        
    async def generate_executive_summary(self, data: Dict[str, Any]) -> bytes:
        """Générer le PDF exécutif complet"""
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Contenu du document
        story = []
        
        # 1. En-tête
        story.append(self._create_header(data))
        story.append(Spacer(1, 20))
        
        # 2. KPIs
        story.append(self._create_kpi_section(data))
        story.append(Spacer(1, 30))
        
        # 3. Graphique donut
        story.append(self._create_donut_chart(data))
        story.append(Spacer(1, 30))
        
        # 4. Recommandations
        story.append(self._create_recommendations_section(data))
        story.append(Spacer(1, 20))
        
        # 5. Tableau départements
        if data.get("departments"):
            story.append(self._create_departments_table(data))
            story.append(Spacer(1, 20))
        
        # 6. Footer
        story.append(self._create_footer())
        
        # Générer le PDF
        doc.build(story)
        
        return buffer.getvalue()
    
    def _create_header(self, data: Dict[str, Any]) -> Table:
        """Créer l'en-tête avec le logo et les informations"""
        
        # Structure de l'en-tête
        header_data = [
            ["LOGO", data.get("title", "Analyse d'optimisation Microsoft 365")],
            ["", f"Données du {data.get('period_start', '')} au {data.get('period_end', '')}"],
            ["", f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"]
        ]
        
        header_table = Table(header_data, colWidths=[3*cm, 14*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0078D4")),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (0, 0), 18),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('HEIGHT', (0, 0), (-1, -1), 3*cm),
        ]))
        
        return header_table
```

## 🧪 Tests et validation

### Tests unitaires
```python
# tests/unit/test_report_service.py
import pytest
from unittest.mock import Mock, AsyncMock

class TestReportService:
    
    @pytest.mark.asyncio
    async def test_generate_pdf_report_success(self, db_session, sample_analysis_data):
        """Test génération réussie d'un rapport PDF"""
        
        service = ReportService(db_session)
        
        report = await service.generate_pdf_report(
            analysis_id=sample_analysis_data["analysis_id"],
            generated_by="admin@example.com"
        )
        
        assert report.report_type == "PDF"
        assert report.file_name.endswith(".pdf")
        assert report.file_size_bytes > 0
        assert "metadata" in report.metadata
        
    @pytest.mark.asyncio
    async def test_generate_excel_report_success(self, db_session, sample_analysis_data):
        """Test génération réussie d'un rapport Excel"""
        
        service = ReportService(db_session)
        
        report = await service.generate_excel_report(
            analysis_id=sample_analysis_data["analysis_id"],
            generated_by="admin@example.com"
        )
        
        assert report.report_type == "EXCEL"
        assert report.file_name.endswith(".xlsx")
        assert report.file_size_bytes > 0
        assert len(report.metadata.get("sheets", [])) == 3
```

### Tests d'intégration
```python
# tests/integration/test_api_reports.py
import pytest
from httpx import AsyncClient

class TestAPIReports:
    
    @pytest.mark.asyncio
    async def test_generate_pdf_report_endpoint(self, client: AsyncClient, auth_headers):
        """Test endpoint génération PDF"""
        
        response = await client.post(
            f"/api/v1/reports/analyses/{test_analysis_id}/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["report_type"] == "PDF"
        assert "download_url" in data
        
    @pytest.mark.asyncio
    async def test_download_report_endpoint(self, client: AsyncClient, auth_headers):
        """Test téléchargement de rapport"""
        
        # Générer d'abord un rapport
        generate_response = await client.post(
            f"/api/v1/reports/analyses/{test_analysis_id}/pdf",
            headers=auth_headers
        )
        report_data = generate_response.json()
        
        # Télécharger le rapport
        download_response = await client.get(
            report_data["download_url"],
            headers=auth_headers
        )
        
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/pdf"
        assert len(download_response.content) > 0
```

## 📋 Critères d'acceptation

### Fonctionnels
- ✅ **Rapport PDF 1 page** avec 6 sections complètes
- ✅ **Fichier Excel 3 feuilles** avec 18 colonnes formatées
- ✅ **Données dynamiques** issues de l'analyse
- ✅ **Formatage Microsoft** (couleurs, polices, mise en page)
- ✅ **Graphiques** (donut chart pour répartition licences)
- ✅ **Formatage conditionnel** (couleurs selon valeurs)

### Techniques
- ✅ **Génération asynchrone** non bloquante
- ✅ **Cache Redis** pour stockage temporaire
- ✅ **TTL 90 jours** pour cleanup automatique
- ✅ **Tests unitaires** (≥10 tests)
- ✅ **Tests d'intégration** (≥5 tests)
- ✅ **Documentation OpenAPI** complète

### Qualité
- ✅ **Code coverage ≥ 95%** sur nouveaux modules
- ✅ **Type hints** complets
- ✅ **Docstrings** pour toutes les fonctions
- ✅ **Logging structuré** avec correlation IDs
- ✅ **Gestion d'erreurs** robuste

## 🚀 API Endpoints

```
# Génération de rapports
POST /api/v1/reports/analyses/{analysis_id}/pdf
POST /api/v1/reports/analyses/{analysis_id}/excel

# Téléchargement des rapports
GET  /api/v1/reports/{report_id}/download
GET  /api/v1/reports/{report_id}  # Métadonnées

# Liste des rapports
GET  /api/v1/reports/analyses/{analysis_id}
GET  /api/v1/reports/tenants/{tenant_id}

# Suppression (soft delete)
DELETE /api/v1/reports/{report_id}
```

## 📦 Dépendances Python

```txt
# requirements.txt (ajouts pour Lot 7)
reportlab==4.0.7          # Génération PDF
openpyxl==3.1.2           # Génération Excel
matplotlib==3.8.2         # Graphiques
Pillow==10.1.0            # Manipulation images
pandas==2.1.4             # Data manipulation
jinja2==3.1.2             # Templates (optionnel)
```

## 🔐 Sécurité et conformité

- **Validation des données** avant génération
- **Sanitization** des noms de fichiers
- **Limites de taille** sur les rapports (max 50MB)
- **TTL automatique** pour éviter accumulation
- **Accès restreint** aux rapports (tenant isolation)
- **Logging audit** de toutes les générations

---

**Status**: ✅ **Prêt pour implémentation**
**Dernière mise à jour**: Novembre 2024
**Version**: 1.0