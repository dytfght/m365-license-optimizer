#!/bin/bash

# Script pour extraire tous les textes français des générateurs et les traduire

echo "🔍 Extraction exhaustive des textes français dans les générateurs"
echo "==================================================================="

cd "/mnt/d/DOC G/Projets/m365-license-optimizer/backend/src/services/reports"

# 1. Extraire les textes français d'excel_generator_simple.py
echo "📊 Analyse d'excel_generator_simple.py..."

python3 << 'PYEOF'
import re
import ast

file_path = "excel_generator_simple.py"
texts_found = []

with open(file_path, 'r') as f:
    content = f.read()
    # Trouver tous les strings en français (caractères accentués)
    pattern = r'=\s*["\']([A-ZÉÈÀÙ][^"\']*[éèàùûêâîôçÉÈÀÙ][^"\']*)["\']'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        if 'i18n_service' not in match.group(0):  # Exclure les lignes déjà traduites
            texts_found.append(match.group(1))

print(f"✅ {len(texts_found)} textes français trouvés:")
for i, text in enumerate(texts_found, 1):
    print(f"  {i}. {text}")

# Générer les clés de traduction nécessaires
translations_needed = {
    "en": {},
    "fr": {}
}

for text in texts_found:
    # Nettoyer pour créer une clé de traduction
    key = text.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    key = re.sub(r'[^a-z0-9_]', '', key)
    
    # Traduire approximativement (à améliorer manuellement)
    translations_needed["en"][f"report.{key}"] = text  # Par défaut, garder tel quel pour review
    translations_needed["fr"][f"report.{key}"] = text

print("\n📋 Clés de traduction à ajouter:")
for key in translations_needed["en"]:
    print(f'"{key}": "{translations_needed["en"][key]}",')
PYEOF

echo ""
echo "📄 Analyse du PDFGenerator..."
python3 << 'PYEOF'
file_path = "pdf_generator.py"
texts_found = []

with open(file_path, 'r') as f:
    content = f.read()
    # Trouver les textes en français et les f-strings avec texte français
    patterns = [
        r'=\s*["\']([A-ZÉÈÀÙ][^"\']*[éèàùûêâîôçÉÈÀÙ][^"\']*)["\']',
        r'f["\'][^"\']*([A-ZÉÈÀÙ][^"\']*[éèàùûêâîôçÉÈÀÙ][^"\']*)[^"\']*["\']',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            if 'i18n_service' not in match.group(0):
                texts_found.append(match.group(1))

print(f"✅ {len(texts_found)} textes français trouvés:")
for i, text in enumerate(texts_found, 1):
    print(f"  {i}. {text}")
PYEOF

echo ""
echo "🎯 RÉSUMÉ:"
echo "==========="
echo "Les textes ci-dessus doivent TOUS être remplacés par:"
echo "  i18n_service.translate('report.clé', language)"
echo ""
echo "Clés à ajouter dans i18n_service.py: report.*"
