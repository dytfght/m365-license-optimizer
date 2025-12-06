#!/usr/bin/env python3
"""
Database Backup Script for LOT 11
Backs up PostgreSQL database to Azure Blob Storage using Managed Identity.
"""
import argparse
import gzip
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4


def create_backup(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    output_path: Path,
    compress: bool = True,
) -> Optional[Path]:
    """
    Create a PostgreSQL backup using pg_dump.

    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        output_path: Output file path
        compress: Whether to compress the backup

    Returns:
        Path to backup file if successful, None otherwise
    """
    env = os.environ.copy()
    env["PGPASSWORD"] = password

    cmd = [
        "pg_dump",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", database,
        "--format=custom",
        "--compress=9" if compress else "--no-compression",
        "-f", str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            print(f"ERROR: pg_dump failed: {result.stderr}")
            return None

        return output_path

    except subprocess.TimeoutExpired:
        print("ERROR: Backup timed out after 10 minutes")
        return None
    except FileNotFoundError:
        print("ERROR: pg_dump not found. Install PostgreSQL client tools.")
        return None
    except Exception as e:
        print(f"ERROR: Backup failed: {e}")
        return None


def upload_to_azure_blob(
    file_path: Path,
    storage_account: str,
    container: str,
    blob_name: Optional[str] = None,
) -> Optional[str]:
    """
    Upload a file to Azure Blob Storage using Managed Identity.

    Args:
        file_path: Path to the file to upload
        storage_account: Azure Storage account name
        container: Container name
        blob_name: Optional blob name (defaults to filename)

    Returns:
        Blob URL if successful, None otherwise
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)

        container_client = blob_service_client.get_container_client(container)

        # Create container if it doesn't exist
        try:
            container_client.create_container()
            print(f"Created container: {container}")
        except Exception:
            pass  # Container already exists

        blob_name = blob_name or file_path.name
        blob_client = container_client.get_blob_client(blob_name)

        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        blob_url = f"{account_url}/{container}/{blob_name}"
        print(f"Uploaded to: {blob_url}")
        return blob_url

    except ImportError:
        print("ERROR: Azure SDK not installed. Run: pip install azure-identity azure-storage-blob")
        return None
    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        return None


def cleanup_old_backups(
    storage_account: str,
    container: str,
    retention_days: int = 30,
) -> int:
    """
    Delete backups older than retention_days.

    Args:
        storage_account: Azure Storage account name
        container: Container name
        retention_days: Number of days to retain backups

    Returns:
        Number of deleted backups
    """
    try:
        from datetime import timedelta

        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        account_url = f"https://{storage_account}.blob.core.windows.net"
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(account_url, credential=credential)

        container_client = blob_service_client.get_container_client(container)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        deleted_count = 0
        for blob in container_client.list_blobs():
            if blob.last_modified and blob.last_modified < cutoff_date:
                if blob.name.startswith("backup_"):
                    container_client.delete_blob(blob.name)
                    print(f"Deleted old backup: {blob.name}")
                    deleted_count += 1

        return deleted_count

    except ImportError:
        print("WARNING: Azure SDK not installed, skipping cleanup")
        return 0
    except Exception as e:
        print(f"WARNING: Cleanup failed: {e}")
        return 0


def main():
    """Main entry point for backup script."""
    parser = argparse.ArgumentParser(
        description="Database backup for M365 License Optimizer"
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
        "--local-only",
        action="store_true",
        help="Only create local backup, don't upload to Azure",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./backups"),
        help="Local output directory for backups",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.environ.get("BACKUP_RETENTION_DAYS", "30")),
        help="Number of days to retain backups",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old backups after creating new one",
    )

    args = parser.parse_args()

    # Validate password
    if not args.password:
        print("ERROR: Database password required. Set POSTGRES_PASSWORD or use --password")
        sys.exit(1)

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_id = str(uuid4())[:8]
    filename = f"backup_{timestamp}_{backup_id}.dump"
    backup_path = args.output_dir / filename

    print(f"\n{'='*60}")
    print("M365 License Optimizer - Database Backup")
    print(f"{'='*60}")
    print(f"Timestamp: {timestamp}")
    print(f"Database: {args.database}@{args.host}:{args.port}")
    print(f"Output: {backup_path}")
    print(f"{'='*60}\n")

    # Create backup
    print("Creating database backup...")
    result = create_backup(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
        output_path=backup_path,
    )

    if not result:
        print("\n❌ Backup failed!")
        sys.exit(1)

    file_size = backup_path.stat().st_size
    print(f"✓ Backup created: {filename} ({file_size / 1024 / 1024:.2f} MB)")

    # Upload to Azure if configured
    if not args.local_only and args.storage_account:
        print("\nUploading to Azure Blob Storage...")
        blob_url = upload_to_azure_blob(
            backup_path,
            args.storage_account,
            args.container,
        )

        if blob_url:
            print(f"✓ Uploaded to: {blob_url}")

            # Optional cleanup
            if args.cleanup:
                print(f"\nCleaning up backups older than {args.retention_days} days...")
                deleted = cleanup_old_backups(
                    args.storage_account,
                    args.container,
                    args.retention_days,
                )
                print(f"✓ Deleted {deleted} old backup(s)")
        else:
            print("⚠ Upload failed, backup saved locally")

    elif not args.storage_account and not args.local_only:
        print("\n⚠ AZURE_STORAGE_ACCOUNT not configured, backup saved locally only")

    print(f"\n{'='*60}")
    print("✅ Backup completed successfully!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
