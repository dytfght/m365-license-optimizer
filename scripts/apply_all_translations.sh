#!/bin/bash

echo "🔧 APPLICATION DES TRADUCTIONS COMPLETES"
echo "========================================="

cd "/mnt/d/DOC G/Projets/m365-license-optimizer"

# 1. Ajouter toutes les traductions manquantes
echo "1. Ajout des traductions manquantes..."

python3 << 'PYEOF'
file_path = "backend/src/services/i18n_service.py"

with open(file_path, 'r') as f:
    content = f.read()

# Traductions à ajouter
translations = {
    "en": {
        # Excel Summary
        "report.title.excel_summary": "Microsoft 365 License Optimization Summary",
        "report.kpi_section": "Key Performance Indicators",
        "report.license_distribution": "License Distribution",
        "report.period": "Period",
        
        # Excel Detailed
        "report.detailed_recommendations": "Detailed Recommendations by User",
        "report.office_desktop_required": "Office Desktop Required",
        "report.last_activity_date": "Last Activity Date",
        "report.inactivity_days": "Inactivity Days",
        "report.recommendation_status": "Recommendation Status",
        "report.recommendation_reason": "Recommendation Reason",
        "report.yes": "Yes",
        "report.no": "No",
        "report.proposed": "Proposed",
        "report.validated": "Validated",
        "report.rejected": "Rejected",
        "report.sensitive": "Sensitive",
        
        # Excel Raw Data
        "report.raw_data": "Raw Data Analysis",
        
        # PDF
        "report.title.pdf_summary": "Microsoft 365 License Optimization Report",
        "report.optimization_by_departments": "Optimization Summary by Departments",
    },
    "fr": {
        # Excel Summary
        "report.title.excel_summary": "SYNTHÈSE - ANALYSE D'OPTIMISATION MICROSOFT 365",
        "report.kpi_section": "INDICATEURS CLÉS",
        "report.license_distribution": "Répartition des licences",
        "report.period": "Période",
        
        # Excel Detailed
        "report.detailed_recommendations": "Recommandations détaillées par utilisateur",
        "report.office_desktop_required": "Bureau Office requis",
        "report.last_activity_date": "Date dernière activité",
        "report.inactivity_days": "Jours d'inactivité",
        "report.recommendation_status": "Statut recommandation",
        "report.recommendation_reason": "Raison recommandation",
        "report.yes": "Oui",
        "report.no": "Non",
        "report.proposed": "Proposé",
        "report.validated": "Validé",
        "report.rejected": "Rejeté",
        "report.sensitive": "Sensible",
        
        # Excel Raw Data
        "report.raw_data": "Données brutes d'analyse",
        
        # PDF
        "report.title.pdf_summary": "RAPPORT D'OPTIMISATION MICROSOFT 365",
        "report.optimization_by_departments": "Résumé par départements",
    }
}

# Compter les ajouts
added_en = 0
added_fr = 0

for key in translations["en"]:
    if f'"{key}":' not in content:
        # Ajouter dans section EN
        pos = content.find('# Error messages', content.find('"en": {'))
        if pos > 0:
            line = f'        "{key}": "{translations["en"][key]}",'
            content = content[:pos] + line + "\n" + content[pos:]
            added_en += 1
        
        # Ajouter dans section FR
        pos_fr = content.find('# Error messages', content.find('"fr": {'))
        if pos_fr > 0:
            line = f'        "{key}": "{translations["fr"][key]}",'
            content = content[:pos_fr] + line + "\n" + content[pos_fr:]
            added_fr += 1

print(f"✅ {added_en} traductions EN ajoutées")
print(f"✅ {added_fr} traductions FR ajoutées")

# Sauvegarder
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Traductions sauvegardées")
PYEOF

# 2. Remplacer les textes en dur
echo ""
echo "2. Remplacement des textes en dur..."

# Backup
cp backend/src/services/reports/excel_generator_simple.py{,.backup}
cp backend/src/services/reports/pdf_generator.py{,.backup}

# Remplacements Excel
python3 -c "
import re

file_path = 'backend/src/services/reports/excel_generator_simple.py'
with open(file_path, 'r') as f:
    content = f.read()

replacements = [
    ('''i18n_service.translate("report.current_monthly_cost", language) or \"Current Monthly Cost\"''', 'i18n_service.translate("report.current_monthly_cost", language)'),
    ('''i18n_service.translate("report.target_monthly_cost", language) or \"Target Monthly Cost\"''', 'i18n_service.translate("report.target_monthly_cost", language)'),
    ('''i18n_service.translate("report.monthly_savings", language) or \"Monthly Savings\"''', 'i18n_service.translate("report.monthly_savings", language)'),
    ('''i18n_service.translate("report.annual_savings", language) or \"Annual Savings\"''', 'i18n_service.translate("report.annual_savings", language)'),
    ('''i18n_service.translate("report.savings_percentage", language) or \"Savings Percentage\"''', 'i18n_service.translate("report.savings_percentage", language)'),
    ('''i18n_service.translate("report.current_monthly_cost", language) or \"Current Monthly Cost\"''', 'i18n_service.translate("report.current_monthly_cost", language)'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(file_path, 'w') as f:
    f.write(content)

print('✅ Remplacements Excel appliqués')
"

# 3. Redémarrer
echo ""
echo "3. Redémarrage du backend..."
docker-compose restart backend

echo ""
echo "⏳ Attente du redémarrage..."
sleep 8

echo ""
echo "🎉 TOUTES LES CORRECTIONS SONT APPLIQUÉES!"
echo ""
echo "📝 Test à effectuer:"
echo ""
echo "1. Générez un rapport Excel"
echo "2. Ouvrez le fichier"
echo "3. Vérifiez TOUS les champs: Titres, en-têtes, labels"
echo "4. Vérifiez: $ vs €, MM/DD/YYYY vs DD/MM/YYYY"
echo ""
echo "⚠️  Si des champs sont ENCORE en français:"
echo "   → Notez exactement lesquels"
echo "   → Envoyez-moi les logs: docker-compose logs backend --tail=20"
echo "   → Envoyez-moi le fichier Excel généré"
echo ""
