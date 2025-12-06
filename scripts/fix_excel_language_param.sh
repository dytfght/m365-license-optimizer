#!/bin/bash

echo "🔧 CORRECTION: Passer 'language' aux méthodes privées"
echo "======================================================"

cd "/mnt/d/DOC G/Projets/m365-license-optimizer/backend/src/services/reports"

# Corriger le fichier ExcelGenerator
echo "1️⃣ Correction d'ExcelGenerator..."

python3 << 'PYEOF'
# Lire le fichier
file_path = "excel_generator_simple.py"
with open(file_path, 'r') as f:
    content = f.read()

# Ajouter paramètre language aux méthodes privées
replacements = [
    # Définitions de méthodes
    ('def _create_summary_sheet(self, wb: Workbook, data: Dict[str, Any], sheet_name: str):',
     'def _create_summary_sheet(self, wb: Workbook, data: Dict[str, Any], sheet_name: str, language: str):'),
    
    ('def _create_detailed_sheet(self, wb: Workbook, data: Dict[str, Any], sheet_name: str):',
     'def _create_detailed_sheet(self, wb: Workbook, data: Dict[str, Any], sheet_name: str, language: str):'),
    
    ('def _create_raw_data_sheet(self, wb: Workbook, data: Dict[str, Any], sheet_name: str):',
     'def _create_raw_data_sheet(self, wb: Workbook, data: Dict[str, Any], sheet_name: str, language: str):'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Corriger les appels dans generate_detailed_excel
old_calls = '''        # Generate each sheet
        self._create_summary_sheet(wb, data, sheet_names[0])
        self._create_detailed_sheet(wb, data, sheet_names[1])
        self._create_raw_data_sheet(wb, data, sheet_names[2])'''

new_calls = '''        # Generate each sheet
        self._create_summary_sheet(wb, data, sheet_names[0], language)
        self._create_detailed_sheet(wb, data, sheet_names[1], language)
        self._create_raw_data_sheet(wb, data, sheet_names[2], language)'''

content = content.replace(old_calls, new_calls)

# Écrire le fichier
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Corrections appliquées dans excel_generator_simple.py")
PYEOF

echo ""
echo "🔄 Redémarrage du backend..."
docker-compose restart backend

echo ""
echo "⏳ Attente (10s)..."
sleep 10

echo ""
echo "✅ CORRECTION TERMINÉE!"
echo ""
echo "📝 Le paramètre 'language' est maintenant passé à toutes les méthodes."
echo ""
echo "Testez à nouveau la génération d'Excel!"
