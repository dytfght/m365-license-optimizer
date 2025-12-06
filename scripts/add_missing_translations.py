#!/usr/bin/env python3
"""
Ajouter les clés de traduction manquantes dans i18n_service.py
"""

print("📝 Vérification et ajout des traductions manquantes...")
print("=" * 60)

file_path = "backend/src/services/i18n_service.py"

with open(file_path, 'r') as f:
    content = f.read()

# Clés nécessaires pour les rapports
translations_needed = {
    "en": {
        "report.title.excel_summary": "Microsoft 365 License Optimization Summary",
        "report.generated_at": "Report generated",
        "report.kpi_section": "Key Performance Indicators",
        "report.current_monthly_cost": "Current Monthly Cost",
        "report.target_monthly_cost": "Target Monthly Cost",
        "report.monthly_savings": "Monthly Savings",
        "report.annual_savings": "Annual Savings",
        "report.savings_percentage": "Savings Percentage",
        "report.title.pdf_summary": "Microsoft 365 License Optimization Report Summary",
        "period": "Period",
    },
    "fr": {
        "report.title.excel_summary": "SYNTHÈSE - ANALYSE D'OPTIMISATION MICROSOFT 365",
        "report.generated_at": "Date de génération",
        "report.kpi_section": "INDICATEURS CLÉS",
        "report.current_monthly_cost": "Coût actuel mensuel",
        "report.target_monthly_cost": "Coût cible mensuel",
        "report.monthly_savings": "Économie mensuelle",
        "report.annual_savings": "Économie annuelle",
        "report.savings_percentage": "Taux d'économie",
        "report.title.pdf_summary": "RAPPORT D'OPTIMISATION MICROSOFT 365",
        "period": "Période",
    }
}

# Vérifier quelles clés manquent
missing_en = []
missing_fr = []

for key in translations_needed["en"]:
    if f'"{key}":' not in content:
        missing_en.append(key)
        missing_fr.append(key)

if missing_en:
    print(f"⚠️  {len(missing_en)} clés de traduction manquantes:")
    for key in missing_en:
        print(f"   - {key}")
    
    print("")
    print("✅ Ajout des clés manquantes...")
    
    # Localiser la section "en" dans translations
    en_section_start = content.find('"en": {')
    if en_section_start == -1:
        print("❌ Impossible de trouver la section 'en'")
        exit(1)
    
    # Insérer les clés manquantes dans la section EN
    insert_pos = en_section_start + 6  # Après "en": {
    
    en_insertions = []
    for key in missing_en:
        value = translations_needed["en"][key]
        en_insertions.append(f'        "{key}": "{value}",')
    
    en_block = "\n".join(en_insertions)
    content = content[:insert_pos] + "\n" + en_block + content[insert_pos:]
    
    # Maintenant insérer dans la section FR (il faut trouver où elle commence)
    fr_section_start = content.find('"fr": {', insert_pos)
    if fr_section_start == -1:
        print("❌ Impossible de trouver la section 'fr'")
        exit(1)
    
    insert_pos = fr_section_start + 6  # Après "fr": {
    
    fr_insertions = []
    for key in missing_fr:
        value = translations_needed["fr"][key]
        fr_insertions.append(f'        "{key}": "{value}",')
    
    fr_block = "\n".join(fr_insertions)
    content = content[:insert_pos] + "\n" + fr_block + content[insert_pos:]
    
    # Sauvegarder
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ {len(missing_en)} clés ajoutées avec succès!")
    
else:
    print("✅ Toutes les clés de traduction sont présentes!")

print("")
print("=" * 60)
print("🎉 Procédure terminée!")
print("")
print("📝 Prochaines étapes:")
print("   1. Redémarrez le backend: docker-compose restart backend")
print("   2. Générez un rapport")
print("   3. Vérifiez que les titres sont dans la bonne langue")
print("")
