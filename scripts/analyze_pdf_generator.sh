#!/bin/bash

echo "🔍 Analyse exhaustive du PDFGenerator pour textes français"
echo "==========================================================="

cd "/mnt/d/DOC G/Projets/m365-license-optimizer/backend/src/services/reports"

python3 << 'PYEOF'
import re

file_path = "pdf_generator.py"

with open(file_path, 'r') as f:
    content = f.read()

# Extraction de TOUS les textes en français
pattern = r'=\s*["\']([^"\']*[éèàùûêâîôçÉÈÀÙ][^"\']*)["\']'
matches = re.finditer(pattern, content)

textes_fr = []
for match in matches:
    text = match.group(1)
    if len(text) > 3 and 'i18n_service' not in text:  # Ignorer les textes courts et déjà traduits
        textes_fr.append(text)

print(f"🔢 {len(textes_fr)} textes français trouvés dans PDFGenerator:\n")

for i, text in enumerate(textes_fr, 1):
    print(f"{i:2d}. {text}")

# Générer les clés de traduction
print(f"\n📋 Clés de traduction à ajouter:\n")
for text in textes_fr:
    key = text.strip().lower().replace(" ", "_").replace("-", "_").replace("'", "")
    key = re.sub(r'[^a-z0-9_]', '', key)
    key = key[:50]
    print(f'"report.{key}": "{text}",')

PYEOF

echo ""
echo "✅ Analyse terminée"
echo ""
echo "📝 Prochaine étape: Copier les clés ci-dessus et les ajouter"
echo "   dans backend/src/services/i18n_service.py"
echo "   PUIS remplacer chaque texte par i18n_service.translate(...)"
