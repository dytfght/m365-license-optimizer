#!/usr/bin/env python3
"""
Script pour nettoyer les espaces blancs dans les fichiers Python
"""
import os
import re

def cleanup_file(filepath):
    """Nettoie les espaces blancs dans un fichier"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Supprime les espaces blancs en fin de ligne
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Supprime les espaces blancs en fin de ligne
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)
        
        # Rejoint les lignes
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Ajoute une nouvelle ligne à la fin si nécessaire
        if not cleaned_content.endswith('\n'):
            cleaned_content += '\n'
        
        # Écrit le fichier nettoyé
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
            
        return True
    except Exception as e:
        print(f"Erreur avec {filepath}: {e}")
        return False

def main():
    """Nettoie tous les fichiers Python dans le backend"""
    backend_dir = "/mnt/d/DOC G/Projets/m365-license-optimizer/backend"
    
    for root, dirs, files in os.walk(backend_dir):
        # Ignore les dossiers __pycache__ et .git
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if cleanup_file(filepath):
                    print(f"✅ Nettoyé: {filepath}")
                else:
                    print(f"❌ Erreur: {filepath}")

if __name__ == "__main__":
    main()