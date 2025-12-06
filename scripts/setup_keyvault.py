#!/usr/bin/env python3
"""
Azure Key Vault Integration Script for LOT 11
Fetches secrets from Azure Key Vault using Managed Identity.
"""
import argparse
import os
import sys
from typing import Optional


def get_secret_from_keyvault(
    vault_url: str,
    secret_name: str,
) -> Optional[str]:
    """
    Retrieve a secret from Azure Key Vault using Managed Identity.

    Args:
        vault_url: The URL of the Azure Key Vault (e.g., https://myvault.vault.azure.net/)
        secret_name: The name of the secret to retrieve

    Returns:
        The secret value, or None if retrieval failed
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        # DefaultAzureCredential will use:
        # 1. Managed Identity in Azure
        # 2. Azure CLI credentials locally
        # 3. Environment variables (AZURE_CLIENT_ID, etc.)
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)

        secret = client.get_secret(secret_name)
        return secret.value

    except ImportError:
        print("ERROR: Azure SDK not installed. Run: pip install azure-identity azure-keyvault-secrets")
        return None
    except Exception as e:
        print(f"ERROR: Failed to retrieve secret '{secret_name}': {e}")
        return None


def list_secrets(vault_url: str) -> list[str]:
    """
    List all secret names in the Key Vault.

    Args:
        vault_url: The URL of the Azure Key Vault

    Returns:
        List of secret names
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)

        secrets = []
        for secret_properties in client.list_properties_of_secrets():
            secrets.append(secret_properties.name)
        return secrets

    except ImportError:
        print("ERROR: Azure SDK not installed. Run: pip install azure-identity azure-keyvault-secrets")
        return []
    except Exception as e:
        print(f"ERROR: Failed to list secrets: {e}")
        return []


def export_env_vars(vault_url: str, secret_names: list[str]) -> dict[str, str]:
    """
    Export multiple secrets as environment variables.

    Args:
        vault_url: The URL of the Azure Key Vault
        secret_names: List of secret names to export

    Returns:
        Dictionary of secret name to value mappings
    """
    env_vars = {}
    for name in secret_names:
        value = get_secret_from_keyvault(vault_url, name)
        if value:
            env_key = name.upper().replace("-", "_")
            env_vars[env_key] = value
            os.environ[env_key] = value
            print(f"Exported: {env_key}")
    return env_vars


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Azure Key Vault integration for M365 License Optimizer"
    )
    parser.add_argument(
        "--vault-url",
        default=os.environ.get("AZURE_KEYVAULT_URL", ""),
        help="Azure Key Vault URL (or set AZURE_KEYVAULT_URL env var)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all secret names in the Key Vault",
    )
    parser.add_argument(
        "--get",
        metavar="SECRET_NAME",
        help="Get a specific secret value",
    )
    parser.add_argument(
        "--export",
        nargs="+",
        metavar="SECRET_NAME",
        help="Export secrets as environment variables",
    )
    parser.add_argument(
        "--export-all",
        action="store_true",
        help="Export all secrets as environment variables",
    )

    args = parser.parse_args()

    if not args.vault_url:
        print("ERROR: --vault-url required or set AZURE_KEYVAULT_URL environment variable")
        sys.exit(1)

    if args.list:
        secrets = list_secrets(args.vault_url)
        print(f"\nSecrets in {args.vault_url}:")
        for name in secrets:
            print(f"  - {name}")
        print(f"\nTotal: {len(secrets)} secrets")

    elif args.get:
        value = get_secret_from_keyvault(args.vault_url, args.get)
        if value:
            print(f"{args.get}={value}")
        else:
            sys.exit(1)

    elif args.export:
        export_env_vars(args.vault_url, args.export)

    elif args.export_all:
        secrets = list_secrets(args.vault_url)
        export_env_vars(args.vault_url, secrets)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
