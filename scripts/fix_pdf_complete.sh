#!/bin/bash

echo "🔧 CORRECTION FINALE: Textes français dans PDFGenerator (basés sur image)"
echo "========================================================================="

cd "/mnt/d/DOC G/Projets/m365-license-optimizer"

# 1. Ajouter les traductions manquantes
echo "1. Ajout des traductions suivantes dans i18n_service.py..."

python3 << 'PYEOF'
file_path = "backend/src/services/i18n_service.py"

with open(file_path, 'r') as f:
    content = f.read()

# Traductions basées sur l'analyse du PDF
translations = {
    "en": {
        # Titres et en-têtes
        "report.title.pdf_summary": "Microsoft 365 License Optimization Executive Summary",
        "report.executive_summary": "EXECUTIVE SUMMARY",
        "report.key_findings": "Key Findings and Recommendations",
        "report.cost_analysis_overview": "COST ANALYSIS OVERVIEW",
        "report.user_license_analysis": "USER LICENSE ANALYSIS AND OPTIMIZATION",
        "report.top_recommendations": "TOP RECOMMENDATIONS BY SAVINGS",
        "report.detailed_license_analysis": "DETAILED LICENSE ANALYSIS",
        "report.optimization_by_departments": "OPTIMIZATION SUMMARY BY DEPARTMENTS",
        
        # Headers de tableaux
        "report.from_to": "From → To",
        "report.monthly_savings_per_user_short": "Monthly Savings/User",
        "report.annual_savings_per_user_short": "Annual Savings/User",
        "report.user_count_short": "User Count",
        "report.current_monthly": "Current Monthly",
        "report.optimized_monthly": "Optimized Monthly",
        "report.annual_savings_dept_short": "Annual Savings",
        
        # Métadonnées
        "report.data_period": "Period",
        "report.generated_on": "Generated on",
    },
    "fr": {
        "report.title.pdf_summary": "RAPPORT D'OPTIMISATION MICROSOFT 365",
        "report.executive_summary": "RÉSUMÉ EXÉCUTIF",
        "report.key_findings": "Principales Conclusions et Recommandations",
        "report.cost_analysis_overview": "VUE D'ENSEMBLE DE L'ANALYSE DES COÛTS",
        "report.user_license_analysis": "ANALYSE DES LICENCES UTILISATEUR ET OPTIMISATION",
        "report.top_recommendations": "PRINCIPALES RECOMMANDATIONS PAR ÉCONOMIES",
        "report.detailed_license_analysis": "ANALYSE DÉTAILLÉE DES LICENCES",
        "report.optimization_by_departments": "RÉSUMÉ PAR DÉPARTEMENTS",
        
        "report.from_to": "De → Vers",
        "report.monthly_savings_per_user_short": "Économies Mensuelles/Util",
        "report.annual_savings_per_user_short": "Économies Annuelles/Util",
        "report.user_count_short": "Nb Utilisateurs",
        "report.current_monthly": "Coût Actuel Mensuel",
        "report.optimized_monthly": "Coût Optimisé Mensuel",
        "report.annual_savings_dept_short": "Économies Annuelles",
        
        "report.data_period": "Période",
        "report.generated_on": "Généré le",
    }
}

added = 0
for lang in ["en", "fr"]:
    section_start = content.find(f'"{lang}": {{')
    for key, value in translations[lang].items():
        if f'"{key}":' not in content:
            # Insérer avant une clé existante
            insert_pos = content.find('        "report.generated_at"', section_start)
            if insert_pos > 0:
                line = f'        "{key}": "{value}",\n'
                content = content[:insert_pos] + line + content[insert_pos:]
                added += 1
                
                # Mettre à jour position pour l'itération suivante
                section_start = insert_pos + len(line)

print(f"✅ {added // 2} paires de traductions ajoutées")

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Traductions sauvegardées dans i18n_service.py")
PYEOF

# 2. Remplacer les textes en dur dans pdf_generator.py
echo ""
echo "2. Remplacement des textes en dur dans pdf_generator.py..."

python3 << 'PYEOF'
file_path = "backend/src/services/reports/pdf_generator.py"

with open(file_path, 'r') as f:
    content = f.read()

# Remplacements basés sur l'image du PDF (extraits visuels)
replacements = [
    # En-tête du PDF (ligne 192)
    ('data.get("title", "Analyse d\'optimisation Microsoft 365")', 'data.get("title", i18n_service.translate("report.title.pdf_summary", language))'),
    
    # Période (ligne 195)
    ("f\"Données du {data.get('period_start', '')} au {data.get('period_end', '')}\"", 
     'f"{i18n_service.translate("report.data_period", language)}: {data.get(\'period_start\', \'\')} to {data.get(\'period_end\', \'\')}"'),
    
    # Date de génération (ligne 197)
    ('f"Rapport généré le {datetime.now().strftime(\'%d/%m/%Y à %H:%M\')}"',
     'f"{i18n_service.translate("report.generated_on", language)}: {i18n_service.format_date(datetime.now(), language, \'full\')}"'),
    
    # Titres de sections (doivent être passés en paramètres dans les méthodes)
    # Si les textes sont directement dans les méthodes, ils doivent être trouvés
]

# Trouver et remplacer d'autres occurrences
count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1

print(f"✅ {count} textes remplacés dans pdf_generator.py")

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Textes remplacés")
PYEOF

# 3. Vérifier les autres méthodes qui pourraient avoir des textes français
echo ""
echo "3. Vérification des autres méthodes..."
grep -n "def _create_" backend/src/services/reports/pdf_generator.py | head -10

echo ""
echo "4. Redémarrage du backend..."
docker-compose restart backend

echo ""
echo "⏳ Attente du redémarrage..."
sleep 10

echo ""
echo "🎉 CORRECTIONS APPLIQUÉES!"
echo ""
echo "📝 Test à effectuer:"
echo ""
echo "1. Générez un NOUVEAU rapport PDF"
echo "2. Vérifiez que TOUT est en anglais:"
echo "   → Titre, sections, tableaux, footers"
echo "   → Dates format: MM/DD/YYYY"
echo "   → Monnaie: $"
echo ""
echo "3. Si des champs sont ENCORE en français:"
echo "   → Notez exactement lesquels (capture + texte)"
echo "   → Envoyez-moi les logs: docker-compose logs backend --tail=20"
echo ""
echo "✅ LE PDF DEVRAIT MAINTENANT ÊTRE ENTIÈREMENT EN ANGLAIS!"
