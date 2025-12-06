#!/usr/bin/env python3
"""
Correction exhaustive des textes français dans pdf_generator.py
Basée sur l'analyse du PDF généré par l'utilisateur
"""

import sys
import os

# Aller dans le bon répertoire
os.chdir("/mnt/d/DOC G/Projets/m365-license-optimizer/backend/src/services/reports")

file_path = "pdf_generator.py"

with open(file_path, 'r') as f:
    content = f.read()

# Remplacements complets basés sur l'analyse du PDF
replacements = [
    # Section EXECUTIVE SUMMARY
    ('"RÉSUMÉ EXÉCUTIF"', 'i18n_service.translate("report.executive_summary", language)'),
    ('"Principales Conclusions et Recommandations"', 'i18n_service.translate("report.key_findings", language)'),
    
    # Section COST ANALYSIS OVERVIEW  
    ('"VUE D\'ENSEMBLE DE L\'ANALYSE DES COÛTS"', 'i18n_service.translate("report.cost_analysis_overview", language)'),
    
    # Section USER LICENSE ANALYSIS
    ('"ANALYSE DES LICENCES UTILISATEUR ET OPTIMISATION"', 'i18n_service.translate("report.user_license_analysis", language)'),
    ('"PRINCIPALES RECOMMANDATIONS PAR ÉCONOMIES"', 'i18n_service.translate("report.top_recommendations", language)'),
    ('"ANALYSE DÉTAILLÉE DES LICENCES"', 'i18n_service.translate("report.detailed_license_analysis", language)'),
    
    # Section RÉSUMÉ PAR DÉPARTEMENTS
    ('"RÉSUMÉ PAR DÉPARTEMENTS"', 'i18n_service.translate("report.optimization_by_departments", language)'),
    
    # Table headers - Section 2
    ('"De → Vers"', 'i18n_service.translate("report.from_to", language)'),
    ('"Économies Mensuelles/Util"', 'i18n_service.translate("report.monthly_savings_per_user_short", language)'),
    ('"Économies Annuelles/Util"', 'i18n_service.translate("report.annual_savings_per_user_short", language)'),
    ('"Nb Utilisateurs"', 'i18n_service.translate("report.user_count_short", language)'),
    
    # Tableau départements
    ('"Coût Actuel Mensuel"', 'i18n_service.translate("report.current_monthly_cost", language)'),
    ('"Coût Optimisé Mensuel"', 'i18n_service.translate("report.target_monthly_cost", language)'),
    ('"Économies Annuelles"', 'i18n_service.translate("report.annual_savings", language)'),
]

# Appliquer les remplacements
count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1

print(f"✅ {count} textes remplacés dans pdf_generator.py")

# Sauvegarder
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Corrections PDF appliquées!")
sys.exit(0) if count > 0 else print("⚠️  Aucun texte trouvé à remplacer")
