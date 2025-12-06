#!/usr/bin/env python3
"""
Vérifier l'état de la base de données et de la migration LOT 12
"""
import os
import sys
import asyncio
from pathlib import Path

# Ajouter le backend au path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import inspect, text
from dotenv import load_dotenv

load_dotenv(backend_path / ".env")


async def check_database():
    """Vérifier si la colonne language existe dans la table users"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL non trouvé dans .env")
        return False

    # Convertir l'URL async si nécessaire
    if "asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(database_url)

    try:
        async with engine.connect() as conn:
            # Vérifier si la table users existe
            inspector = inspect(conn.sync_engine)
            tables = inspector.get_table_names(schema="optimizer")

            if "users" not in tables:
                print("❌ Table 'users' non trouvée dans le schéma optimizer")
                return False

            # Vérifier les colonnes
            columns = inspector.get_columns("users", schema="optimizer")
            column_names = [col["name"] for col in columns]

            if "language" in column_names:
                print("✅ Colonne 'language' existe déjà dans la table users")
                return True
            else:
                print("❌ Colonne 'language' manquante dans la table users")
                print(f"Colonnes existantes: {', '.join(column_names[:10])}{'...' if len(column_names) > 10 else ''}")
                return False

    except Exception as e:
        print(f"❌ Erreur lors de la connexion à la base de données: {e}")
        return False
    finally:
        await engine.dispose()


def check_migration_files():
    """Vérifier les fichiers de migration"""
    migrations_path = backend_path / "alembic" / "versions"

    print("\n📁 Fichiers de migration trouvés:")
    files = sorted(migrations_path.glob("*.py"))

    for file in files:
        if "language" in file.name or "merge" in file.name:
            print(f"  📄 {file.name}")

    # Chercher spécifiquement notre migration
    language_migration = migrations_path / "add_language_to_users.py"
    merge_migration = migrations_path / "merge_lot12_i18n_heads.py"

    if language_migration.exists():
        print(f"\n✅ Migration add_language_to_users trouvée")
    else:
        print(f"\n❌ Migration add_language_to_users manquante")

    if merge_migration.exists():
        print(f"✅ Migration merge_lot12_i18n_heads trouvée")
    else:
        print(f"❌ Migration merge_lot12_i18n_heads manquante")

    return language_migration.exists()


def main():
    """Point d'entrée principal"""
    print("🔍 Vérification de l'état du LOT 12 - i18n")
    print("=" * 50)

    # Vérifier les fichiers
    has_migration = check_migration_files()

    # Vérifier la base de données
    print("\n🗄️ Vérification de la base de données:")
    if sys.platform == "win32":
        # Sous Windows, utiliser un event loop différent
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    has_column = asyncio.run(check_database())

    # Résumé
    print("\n📊 Résumé:")
    print(f"  - Migration créée: {'✅' if has_migration else '❌'}")
    print(f"  - Colonne en DB: {'✅' if has_column else '❌'}")

    if has_migration and not has_column:
        print("\n⚡ Action requise:")
        print("  La migration existe mais n'a pas été appliquée.")
        print("  Exécutez: cd backend && alembic upgrade merge_lot12_i18n_heads")
    elif has_migration and has_column:
        print("\n✅ Statut: Le LOT 12 est correctement installé!")
    else:
        print("\n❌ Statut: Problème de configuration")


if __name__ == "__main__":
    main()
