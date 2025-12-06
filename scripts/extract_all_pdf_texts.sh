#!/bin/bash

echo "🔍 Extraction de TOUS les textes potentiels du PDFGenerator"
echo "============================================================"

cd "/mnt/d/DOC G/Projets/m365-license-optimizer/backend/src/services/reports"

echo "📋 Fichier: pdf_generator.py"
echo ""

# Extraire toutes les lignes avec des opérateurs d'assignation (=) qui pourraient contenir du texte
grep -n "=" pdf_generator.py | grep -v "^#" | grep -E '[A-Za-zÉÈÀÙéèàùûêâîôç]' | \
    grep -v "\.py" | grep -v "import" | grep -v "def " | grep -v "if " | \
    grep -v "for " | grep -v "from " | grep -v "return" | grep -v "#"

echo ""
echo "✅ Extraction complète"
echo ""
echo "📝 Pour corriger le PDF:"
echo "   → Ouvrez pdf_generator.py à chaque ligne affichée ci-dessus"
echo "   → Recherchez le texte entre guillemets avec accents"
echo "   → Remplacez par: i18n_service.translate('report.clé', language)"
echo ""
echo "📊 Exemple:"
echo "   Avant: ws['A5'] = 'RÉPARTITION DES LICENCES'"
echo "   Après:  ws['A5'] = i18n_service.translate('report.license_distribution', language)"
echo ""
echo "🆘 Envoyez-moi le PDF généré si vous voulez que je fasse la liste exacte!"
