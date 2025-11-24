#!/usr/bin/env python3
"""
Helper script to generate a Fernet encryption key for LOT4.
Run this to generate a key for ENCRYPTION_KEY in .env file.
"""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key()
    print("Generated Fernet encryption key:")
    print(key.decode())
    print("\nAdd this to your .env file:")
    print(f"ENCRYPTION_KEY={key.decode()}")
