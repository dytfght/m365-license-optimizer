"""
Encryption service for securing sensitive data (client secrets, etc.)
Uses Fernet symmetric encryption from cryptography library.
"""
import structlog
from cryptography.fernet import Fernet, InvalidToken

logger = structlog.get_logger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    Uses Fernet (symmetric encryption) with a key from environment variables.
    """

    def __init__(self, encryption_key: str):
        """
        Initialize encryption service with Fernet key.

        Args:
            encryption_key: Base64-encoded Fernet key from .env

        Raises:
            ValueError: If encryption key is invalid
        """
        try:
            self._fernet = Fernet(encryption_key.encode())
            logger.info("encryption_service_initialized")
        except Exception as e:
            logger.error("encryption_service_init_failed", error=str(e))
            raise ValueError(f"Invalid encryption key: {e}") from e

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string (Fernet token)

        Raises:
            ValueError: If encryption fails
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode())
            encrypted_str = encrypted_bytes.decode()
            logger.debug("string_encrypted", length=len(plaintext))
            return encrypted_str
        except Exception as e:
            logger.error("encryption_failed", error=str(e))
            raise ValueError(f"Encryption failed: {e}") from e

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a Fernet-encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string (Fernet token)

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (invalid token or wrong key)
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty string")

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode())
            plaintext = decrypted_bytes.decode()
            logger.debug("string_decrypted", length=len(plaintext))
            return plaintext
        except InvalidToken as e:
            logger.error("decryption_failed_invalid_token")
            raise ValueError("Decryption failed: invalid token or wrong key") from e
        except Exception as e:
            logger.error("decryption_failed", error=str(e))
            raise ValueError(f"Decryption failed: {e}") from e

    def validate_key(self) -> bool:
        """
        Validate that the encryption key works by testing encrypt/decrypt.

        Returns:
            True if key is valid, False otherwise
        """
        try:
            test_string = "test_encryption_key_validation"
            encrypted = self.encrypt(test_string)
            decrypted = self.decrypt(encrypted)
            return decrypted == test_string
        except Exception:
            return False
