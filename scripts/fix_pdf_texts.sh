#!/bin/bash

# CORRECTIONS EXACTES POUR PDF - Basées sur l'image

# Tous les textes doivent être remplacés dans : backend/src/services/reports/pdf_generator.py

cd "/mnt/d/DOC G/Projets/m365-license-optimizer"

# Ajouter les traductions manquantes dans i18n_service.py
echo "1. Ajout des 13 traductions manquantes..."

python3 << 'PYEOF'
file_path = "backend/src/services/i18n_service.py"

with open(file_path, 'r') as f:
    content = f.read()

# Traductions pour le PDF basées sur l'image
new_translations = {
    "en": {
        # Section 1 - En-tête
        "report.executive_summary": "EXECUTIVE SUMMARY",
        "report.key_findings": "Key Findings and Recommendations",
        
        # Section 2 - Cost Overview
        "report.cost_analysis_overview": "COST ANALYSIS OVERVIEW",
        
        # Section 3 - Recommendations
        "report.user_license_analysis": "USER LICENSE ANALYSIS AND OPTIMIZATION",
        "report.top_recommendations": "TOP RECOMMENDATIONS BY SAVINGS",
        "report.detailed_license_analysis": "DETAILED LICENSE ANALYSIS",
        
        # Section 4 - Departments
        "report.optimization_by_departments": "OPTIMIZATION SUMMARY BY DEPARTMENTS",
        
        # Table headers - Section 2
        "report.from_to": "From → To",
        "report.monthly_savings_per_user_short": "Monthly Savings/User",
        "report.annual_savings_per_user_short": "Annual Savings/User",
        "report.user_count_short": "User Count",
        
        # Department table headers
        "report.current_monthly": "Current Monthly",
        "report.optimized_monthly": "Optimized Monthly",
        "report.annual_savings_dept_short": "Annual Savings",
    },
    "fr": {
        "report.executive_summary": "RÉSUMÉ EXÉCUTIF",
        "report.key_findings": "Principales Conclusions et Recommandations",
        "report.cost_analysis_overview": "VUE D'ENSEMBLE DE L'ANALYSE DES COÛTS",
        "report.user_license_analysis": "ANALYSE DES LICENCES UTILISATEUR ET OPTIMISATION",
        "report.top_recommendations": "PRINCIPALES RECOMMANDATIONS PAR ÉCONOMIES",
        "report.detailed_license_analysis": "ANALYSE DÉTAILLÉE DES LICENCES",
        "report.optimization_by_departments": "RÉSUMÉ DE L'OPTIMISATION PAR DÉPARTEMENTS",
        "report.from_to": "De → Vers",
        "report.monthly_savings_per_user_short": "Économies Mensuelles/Util",
        "report.annual_savings_per_user_short": "Économies Annuelles/Util",
        "report.user_count_short": "Nb Utilisateurs",
        "report.current_monthly": "Coût Actuel Mensuel",
        "report.optimized_monthly": "Coût Optimisé Mensuel",
        "report.annual_savings_dept_short": "Économies Annuelles",
    }
}

added = 0
for lang in ["en", "fr"]:
    section_start = content.find(f'"{lang}": {{')
    for key, value in new_translations[lang].items():
        if f'"{key}":' not in content:
            # Insérer avant une clé existante
            insert_pos = content.find('        "report.generated_at"', section_start)
            if insert_pos > 0:
                line = f'        "{key}": "{value}",\n'
                content = content[:insert_pos] + line + content[insert_pos:]
                added += 1

print(f"✅ {added} traductions préliminaires ajoutées")

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Traductions sauvegardées")
PYEOF

# Générer le script de correction pour pdf_generator.py
echo ""
echo "2. Génération du script de correction PDF..."

cat > /tmp/fix_pdf.py << 'PYEOF'
import re

# Script de correction automatisé pour pdf_generator.py
# Basé sur l'analyse de l'image du PDF

file_path = "backend/src/services/reports/pdf_generator.py"

with open(file_path, 'r') as f:
    content = f.read()

# Dictionnaire de remplacement : avant → après
replacements = [
    # Page 1 - En-tête (maintenant fermé dans la partie PDF)
    
    # Section EXECUTIVE SUMMARY
    ('"RÉSUMÉ EXÉCUTIF"', 'i18n_service.translate("report.executive_summary", language)'),
    ('"Principales Conclusions et Recommandations"', 'i18n_service.translate("report.key_findings", language)'),
    
    # Section COST ANALYSIS OVERVIEW  
    ('"VUE D\'ENSEMBLE DE L\'ANALYSE DES COÛTS"', 'i18n_service.translate("report.cost_analysis_overview", language)'),
    
    # Section USER LICENSE ANALYSIS
    ('"ANALYSE DES LICENCES UTILISATEUR ET OPTIMISATION"', 'i18n_service.translate("report.user_license_analysis", language)'),
    ('"PRINCIPALES RECOMMANDATIONS PAR ÉCONOMIES"', 'i18n_service.translate("report.top_recommendations", language)'),
    ('"ANALYSE DÉTAILLÉE DES LICENCES"', 'i18n_service.translate("report.detailed_license_analysis", language)'),
    
    # Tableau headers (section recommendations)
    ('"De → Vers"', 'i18n_service.translate("report.from_to", language)'),
    ('"Économies Mensuelles/Util"', 'i18n_service.translate("report.monthly_savings_per_user_short", language)'),
    ('"Économies Annuelles/Util"', 'i18n_service.translate("report.annual_savings_per_user_short", language)'),
    ('"Nb Utilisateurs"', 'i18n_service.translate("report.user_count_short", language)'),
    
    # Section OPTIMIZATION SUMMARY BY DEPARTMENTS
    ('"OPTIMIZATION SUMMARY BY DEPARTMENTS"', 'i18n_service.translate("report.optimization_by_departments", language)'),
    
    # Tableau départements
    ('"Coût Actuel Mensuel"', 'i18n_service.translate("report.current_monthly", language)'),
    ('"Coût Optimisé Mensuel"', 'i18n_service.translate("report.optimized_monthly", language)'),
    ('"Économies Annuelles"', 'i18n_service.translate("report.annual_savings_dept_short", language)'),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1

print(f"✅ {count} remplacements appliqués dans pdf_generator.py")

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Corrections PDF sauvegardées")
PYEOF

echo ""
echo "3️⃣ Pour appliquer la correction aux PDF:"
echo "   → Exécutez: python3 /tmp/fix_pdf.py"
echo ""
echo "4️⃣ Redémarrage du backend:"
echo "   → docker-compose restart backend"
echo ""
echo "🎯 Ou manuellement :"
echo "   → Ouvrez pdf_generator.py"
echo "   → Recherchez TOUS les textes entre guillemets"
echo "   → Remplacez les français par i18n_service.translate()"
echo ""

# Exécuter la correction dès maintenant
python3 /tmp/fix_pdf.py

echo ""
echo "✅ CORRECTIONS APPLIQUÉES!"
echo ""
echo "📝 Test à effectuer:"
echo ""
echo "1. Redémarrez le backend: docker-compose restart backend"
echo "2. Attendez 10 secondes"
echo "3. Générez un nouveau PDF"
echo "4. Vérifiez que TOUT est maintenant en anglais!"
echo ""
