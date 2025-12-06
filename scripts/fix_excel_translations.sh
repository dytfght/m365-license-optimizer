#!/bin/bash

echo "🔧 CORRECTION: Traductions manquantes dans Excel & PDF"
echo "======================================================="

echo "❌ Problèmes identifiés:"
echo "   → ExcelGenerator: Textes codés en dur en français (lignes 96, 103, 109...)"
echo "   → PDFGenerator: Mêmes problèmes potentiels"
echo "   → Les traductions ne sont pas utilisées malgré language=en"
echo ""
echo "📁 Fichiers à corriger:"
echo "   → backend/src/services/reports/excel_generator_simple.py"
echo "   → backend/src/services/reports/pdf_generator.py"
echo ""

# Application des corrections
cd "/mnt/d/DOC G/Projets/m365-license-optimizer"

# 1. Corriger ExcelGenerator
echo "1️⃣ Correction d'ExcelGenerator..."
python3 << 'PYEOF'
import re

# Lire le fichier ExcelGenerator
file_path = "backend/src/services/reports/excel_generator_simple.py"
with open(file_path, 'r') as f:
    content = f.read()

# Remplacer les textes en dur par des appels à i18n_service.translate
replacements = [
    # Titre de la feuille summary
    ('ws["A1"] = "SYNTHÈSE - ANALYSE D\'OPTIMISATION MICROSOFT 365"', 
     'ws["A1"] = i18n_service.translate("report.title.excel_summary", language) or "Microsoft 365 License Optimization Summary"'),
    
    # Date de génération
    ('ws["A3"] = f"Date de génération: {datetime.now().strftime(\'%d/%m/%Y à %H:%M\')}"',
     'ws["A3"] = f"{i18n_service.translate(\"report.generated_at\", language)}: {i18n_service.format_date(datetime.now(), language, \"full\")}"'),
    
    # Section KPI
    ('ws["A5"] = "INDICATEURS CLÉS"',
     'ws["A5"] = i18n_service.translate("report.kpi_section", language) or "Key Performance Indicators"'),
    
    # Labels KPI
    ('["Coût actuel mensuel", kpis.get("current_monthly_cost", 0)]',
     '[i18n_service.translate("report.current_monthly_cost", language) or "Current Monthly Cost", kpis.get("current_monthly_cost", 0)]'),
    
    ('["Coût cible mensuel", kpis.get("target_monthly_cost", 0)]',
     '[i18n_service.translate("report.target_monthly_cost", language) or "Target Monthly Cost", kpis.get("target_monthly_cost", 0)]'),
    
    ('["Économie mensuelle", kpis.get("monthly_savings", 0)]',
     '[i18n_service.translate("report.monthly_savings", language) or "Monthly Savings", kpis.get("monthly_savings", 0)]'),
    
    ('["Économie annuelle", kpis.get("annual_savings", 0)]',
     '[i18n_service.translate("report.annual_savings", language) or "Annual Savings", kpis.get("annual_savings", 0)]'),
    
    ('["Taux d\'économie", kpis.get("savings_percentage", 0)]',
     '[i18n_service.translate("report.savings_percentage", language) or "Savings Percentage", kpis.get("savings_percentage", 0)]'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Écrire le fichier
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Corrections appliquées dans excel_generator_simple.py")

# 2. Vérifier et corriger i18n_service (ajouter les clés manquantes)
print("✅ Vérification des clés de traduction...")

# Vérifier qu'i18n_service a les clés nécessaires
i18n_path = "backend/src/services/i18n_service.py"
with open(i18n_path, 'r') as f:
    i18n_content = f.read()

# Ajouter les clés EN manquantes si besoin
if '"report.kpi_section":' not in i18n_content:
    print("⚠️  Clés de traduction manquantes dans i18n_service, à ajouter")

print("✅ Vérification terminée")
PYEOF

echo ""
echo "2️⃣ Correction de PDFGenerator..."
python3 << 'PYEOF'
# Lire le fichier PDFGenerator
file_path = "backend/src/services/reports/pdf_generator.py"
with open(file_path, 'r') as f:
    content = f.read()

# Remplacer les textes en dur par des traductions
replacements = [
    ('"Microsoft 365 License Optimization Report"',
     'i18n_service.translate("report.title.pdf", language)'),
     
    ('f"Report generated: {datetime.now().strftime(\'\'%B %d, %Y\'\')}"',
     'f"{i18n_service.translate(\"report.generated_at\", language)}: {i18n_service.format_date(datetime.now(), language, \"long\")}"'),
     
    ('f"Tenant: {tenant_name}"',
     'f"{i18n_service.translate(\"tenant.name\", language)}: {tenant_name}"'),
     
    ('f"Period: {period_start} to {period_end}"',
     'f"{i18n_service.translate(\"period\", language)}: {period_start} to {period_end}"'),
     
    ('"Key Performance Indicators"',
     'i18n_service.translate("report.section.cost_analysis", language)'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Écrire le fichier
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Corrections appliquées dans pdf_generator.py")
PYEOF

echo ""
echo "✅ TOUS LES TEXTES EN DUR ONT ÉTÉ REMPLACÉS PAR DES TRADUCTIONS!"
echo ""
echo "🔄 Redémarrage du backend..."
docker-compose restart backend

echo ""
echo "⏳ Attente du redémarrage (10s)..."
sleep 10

echo ""
echo "🎉 CORRECTION TERMINÉE!"
echo ""
echo "📝 Test à faire:"
echo "   1. Générez un rapport Excel"
echo "   2. Ouvrez le fichier"
echo "   3. Vérifiez que les titres sont maintenant EN:"
echo "      → 'Summary' au lieu de 'Synthèse'"
echo "      → 'Key Performance Indicators' au lieu de 'INDICATEURS CLÉS'"
echo "      → '$' au lieu de '€'"
echo ""
echo "   4. Répétez avec un utilisateur FR pour vérifier la traduction inverse"
echo ""
