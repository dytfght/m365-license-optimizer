#!/usr/bin/env python3
"""
Database Restore Script for LOT 11
Restores PostgreSQL database from Azure Blob Storage backup using Managed Identity.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def list_backups(
    storage_account: str,
    container: str,
    limit: int = 20,
) -> list[dict]:
    """
    List available backups in Azure Blob Storage.

    Args:
        storage_account: Azure Storage account name
        container: Container name
        limit: Maximum number of backups to list

    Returns:
        List of backup info dictionaries
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)

        container_client = blob_service_client.get_container_client(container)

        backups = []
        for blob in container_client.list_blobs():
            if blob.name.startswith("backup_"):
                backups.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                })

        # Sort by last modified, newest first
        backups.sort(key=lambda x: x["last_modified"], reverse=True)
        return backups[:limit]

    except ImportError:
        print("ERROR: Azure SDK not installed. Run: pip install azure-identity azure-storage-blob")
        return []
    except Exception as e:
        print(f"ERROR: Failed to list backups: {e}")
        return []


def download_backup(
    storage_account: str,
    container: str,
    blob_name: str,
    output_path: Path,
) -> Optional[Path]:
    """
    Download a backup from Azure Blob Storage.

    Args:
        storage_account: Azure Storage account name
        container: Container name
        blob_name: Name of the blob to download
        output_path: Local path to save the file

    Returns:
        Path to downloaded file if successful, None otherwise
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)

        container_client = blob_service_client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob_name)

        with open(output_path, "wb") as f:
            download_stream = blob_client.download_blob()
            f.write(download_stream.readall())

        print(f"Downloaded: {blob_name}")
        return output_path

    except ImportError:
        print("ERROR: Azure SDK not installed. Run: pip install azure-identity azure-storage-blob")
        return None
    except Exception as e:
        print(f"ERROR: Download failed: {e}")
        return None


def restore_backup(
    backup_path: Path,
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    drop_existing: bool = False,
) -> bool:
    """
    Restore a PostgreSQL backup using pg_restore.

    Args:
        backup_path: Path to the backup file
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        drop_existing: Whether to drop and recreate the database

    Returns:
        True if successful, False otherwise
    """
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    if drop_existing:
        # Drop and recreate database
        print("Dropping existing database...")
        drop_cmd = [
            "dropdb",
            "-h", host,
            "-p", str(port),
            "-U", user,
            "--if-exists",
            database,
        ]
        subprocess.run(drop_cmd, env=env, capture_output=True)

        print("Creating new database...")
        create_cmd = [
            "createdb",
            "-h", host,
            "-p", str(port),
            "-U", user,
            database,
        ]
        result = subprocess.run(create_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: Failed to create database: {result.stderr}")
            return False

    # Restore using pg_restore
    print("Restoring database...")
    restore_cmd = [
        "pg_restore",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", database,
        "--no-owner",
        "--no-privileges",
        "--exit-on-error",
        str(backup_path),
    ]

    try:
        result = subprocess.run(
            restore_cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout
        )

        if result.returncode != 0:
            # pg_restore may return non-zero even on success in some cases
            if "error" in result.stderr.lower():
                print(f"ERROR: pg_restore failed: {result.stderr}")
                return False

        return True

    except subprocess.TimeoutExpired:
        print("ERROR: Restore timed out after 30 minutes")
        return False
    except FileNotFoundError:
        print("ERROR: pg_restore not found. Install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"ERROR: Restore failed: {e}")
        return False


def main():
    """Main entry point for restore script."""
    parser = argparse.ArgumentParser(
        description="Database restore for M365 License Optimizer"
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("POSTGRES_HOST", "localhost"),
        help="Database host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("POSTGRES_PORT", "5432")),
        help="Database port",
    )
    parser.add_argument(
        "--database",
        default=os.environ.get("POSTGRES_DB", "m365_optimizer"),
        help="Database name",
    )
    parser.add_argument(
        "--user",
        default=os.environ.get("POSTGRES_USER", "admin"),
        help="Database user",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("POSTGRES_PASSWORD", ""),
        help="Database password (or set POSTGRES_PASSWORD env var)",
    )
    parser.add_argument(
        "--storage-account",
        default=os.environ.get("AZURE_STORAGE_ACCOUNT", ""),
        help="Azure Storage account name",
    )
    parser.add_argument(
        "--container",
        default=os.environ.get("AZURE_STORAGE_CONTAINER", "backups"),
        help="Azure Storage container name",
    )
    parser.add_argument(
        "--backup-name",
        help="Specific backup name to restore (or use --latest)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Restore the most recent backup",
    )
    parser.add_argument(
        "--local-file",
        type=Path,
        help="Restore from local backup file instead of Azure",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_backups",
        help="List available backups",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop and recreate the database before restore",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts",
    )

    args = parser.parse_args()

    # List backups
    if args.list_backups:
        if not args.storage_account:
            print("ERROR: --storage-account required to list backups")
            sys.exit(1)

        print(f"\nAvailable backups in {args.container}:")
        print("-" * 60)
        backups = list_backups(args.storage_account, args.container)
        for b in backups:
            size_mb = b["size"] / 1024 / 1024
            modified = b["last_modified"].strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {b['name']} ({size_mb:.2f} MB) - {modified}")
        if not backups:
            print("  No backups found")
        print()
        return

    # Validate inputs
    if not args.password:
        print("ERROR: Database password required. Set POSTGRES_PASSWORD or use --password")
        sys.exit(1)

    if not args.local_file and not args.storage_account:
        print("ERROR: Either --local-file or --storage-account required")
        sys.exit(1)

    if not args.local_file and not args.backup_name and not args.latest:
        print("ERROR: Either --backup-name, --latest, or --local-file required")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("M365 License Optimizer - Database Restore")
    print(f"{'='*60}")
    print(f"Target Database: {args.database}@{args.host}:{args.port}")

    # Determine backup source
    if args.local_file:
        backup_path = args.local_file
        print(f"Source: Local file - {backup_path}")
    else:
        if args.latest:
            backups = list_backups(args.storage_account, args.container, limit=1)
            if not backups:
                print("ERROR: No backups found")
                sys.exit(1)
            backup_name = backups[0]["name"]
            print(f"Source: Latest backup - {backup_name}")
        else:
            backup_name = args.backup_name
            print(f"Source: Specified backup - {backup_name}")

    print(f"Drop existing: {'Yes' if args.drop_existing else 'No'}")
    print(f"{'='*60}\n")

    # Confirmation
    if not args.force:
        if args.drop_existing:
            print("⚠️  WARNING: This will DROP AND RECREATE the database!")
            print("⚠️  ALL EXISTING DATA WILL BE LOST!")
        else:
            print("⚠️  WARNING: This will overwrite existing data!")

        response = input("\nAre you sure you want to continue? [y/N]: ")
        if response.lower() != "y":
            print("Restore cancelled.")
            sys.exit(0)

    # Download if from Azure
    if not args.local_file:
        print("\nDownloading backup from Azure...")
        with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as tmp:
            backup_path = Path(tmp.name)

        result = download_backup(
            args.storage_account,
            args.container,
            backup_name,
            backup_path,
        )
        if not result:
            sys.exit(1)

    # Restore
    print("\nRestoring database...")
    success = restore_backup(
        backup_path=backup_path,
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
        drop_existing=args.drop_existing,
    )

    # Cleanup temp file
    if not args.local_file and backup_path.exists():
        backup_path.unlink()

    if success:
        print(f"\n{'='*60}")
        print("✅ Database restored successfully!")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("❌ Database restore failed!")
        print(f"{'='*60}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
