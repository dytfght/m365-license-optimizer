#!/bin/bash

echo "🔧 CORRECTION: Forcer l'utilisation de la langue utilisateur (DB)"
echo "======================================================================="

echo "📝 Problème identifié:"
echo "   → Le frontend envoie Accept-Language: fr (navigateur)"
echo "   → Ce qui écrase current_user.language = en (base)"
echo "   → Résultat: rapports toujours en français !"
echo ""
echo "✅ Solution: IGNORER l'header, utiliser TOUJOURS la langue de la base"
echo ""

# Appliquer la correction
cd "/mnt/d/DOC G/Projets/m365-license-optimizer"

# Modifier reports.py pour ignorer complètement l'header
cat > /tmp/correction_reports.py << 'EOF'
import re

# Lire le fichier
file_path = "backend/src/api/v1/endpoints/reports.py"
with open(file_path, 'r') as f:
    content = f.read()

# Remplacer la logique de détection de langue
old_logic = '''    # Determine language preference - prioritize user's saved preference over browser header
    # Default Accept-Language header is "en", but we should use what's in database
    language = current_user.language
    if accept_language and accept_language != current_user.language:
        # Only override if header is different from user's preference
        header_lang = accept_language.split(",")[0].split("-")[0]
        if header_lang in ["fr", "en"]:
            language = header_lang'''

new_logic = '''    # Determine language preference - USE ONLY USER'S SAVED PREFERENCE FROM DATABASE
    # Ignore Accept-Language header completely to respect user's choice
    # This ensures reports are in the same language as the UI
    language = current_user.language
    
    logger.debug(
        "language_selected_for_report",
        user_preference=current_user.language,
        header_provided=accept_language,
        final_language=language,
        message="Using user preference from database, ignoring header"
    )'''

content = content.replace(old_logic, new_logic)

# Écrire le fichier modifié
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Correction appliquée dans reports.py")
EOF

python3 /tmp/correction_reports.py

echo ""
echo "🔄 Redémarrage du backend..."
docker-compose restart backend

echo ""
echo "⏳ Attente du redémarrage (10s)..."
sleep 10

echo ""
echo "✅ CORRECTION APPLIQUÉE!"
echo ""
echo "📋 Changements:"
echo "   → La langue utilisateur depuis la DB est maintenant PRIORITAIRE"
echo "   → L'header Accept-Language du navigateur est IGNORÉ"
echo "   → Les rapports suivront la langue de l'interface"
echo ""
echo "🧪 TEST À FAIRE:"
echo ""
echo "1. Assurez-vous que votre utilisateur a language='en' dans la base:"
echo "   → docker-compose exec db psql -U admin -d m365_optimizer"
echo "   → SELECT email, language FROM optimizer.users WHERE email='votre@email';"
echo ""
echo "2. Connectez-vous à l'application (interface devrait être EN)"
echo ""
echo "3. Générez un rapport PDF ou Excel:"
echo "   → Le rapport DOIT être en anglais (titre, dates, $)"
echo ""
echo "4. Si c'est toujours en français:"
echo "   → docker-compose logs backend --tail=20"
echo "   → Copiez les lignes avec 'language_selected_for_report'"
echo "   → Elles indiqueront quelle langue est réellement utilisée"
echo ""
echo "🚀 Testez maintenant!"
