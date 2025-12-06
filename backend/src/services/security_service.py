"""
Security Service for LOT 10: Advanced security features
Provides 2FA TOTP, enhanced password hashing, and security validations.
"""
import re
import secrets
from typing import Optional

import pyotp
import structlog
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

logger = structlog.get_logger(__name__)


class SecurityService:
    """
    Service for advanced security operations.
    Provides 2FA TOTP, Argon2 hashing, and input validation.
    """

    def __init__(self):
        """Initialize security service with Argon2 password hasher."""
        self._password_hasher = PasswordHasher(
            time_cost=3,  # Number of iterations
            memory_cost=65536,  # 64MB memory usage
            parallelism=4,  # Number of parallel threads
            hash_len=32,  # Length of the hash
            salt_len=16,  # Length of the salt
        )
        logger.info("security_service_initialized")

    # ============================================
    # 2FA TOTP Operations
    # ============================================

    def generate_totp_secret(self) -> str:
        """
        Generate a new TOTP secret for 2FA setup.

        Returns:
            Base32-encoded secret key

        Example:
            >>> service = SecurityService()
            >>> secret = service.generate_totp_secret()
            >>> print(secret)  # e.g., 'JBSWY3DPEHPK3PXP'
        """
        secret = pyotp.random_base32()
        logger.debug("totp_secret_generated")
        return secret

    def get_totp_provisioning_uri(
        self, secret: str, user_email: str, issuer: str = "M365LicenseOptimizer"
    ) -> str:
        """
        Generate a provisioning URI for QR code generation.

        Args:
            secret: TOTP secret key
            user_email: User's email address
            issuer: Application name shown in authenticator app

        Returns:
            otpauth:// URI for QR code generation
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user_email, issuer_name=issuer)
        logger.debug("totp_provisioning_uri_generated", email=user_email)
        return uri

    def verify_totp(self, secret: str, token: str, valid_window: int = 1) -> bool:
        """
        Verify a TOTP token against the secret.

        Args:
            secret: User's TOTP secret
            token: 6-digit token from authenticator app
            valid_window: Number of 30-second windows to check (default: 1)

        Returns:
            True if token is valid, False otherwise
        """
        if not secret or not token:
            logger.warning("totp_verification_failed", reason="missing_input")
            return False

        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(token, valid_window=valid_window)

            if is_valid:
                logger.info("totp_verification_success")
            else:
                logger.warning("totp_verification_failed", reason="invalid_token")

            return is_valid
        except Exception as e:
            logger.error("totp_verification_error", error=str(e))
            return False

    def get_current_totp(self, secret: str) -> str:
        """
        Get the current TOTP token for a secret (useful for testing).

        Args:
            secret: TOTP secret key

        Returns:
            Current 6-digit TOTP token
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    # ============================================
    # Argon2 Password Hashing
    # ============================================

    def hash_password_argon2(self, password: str) -> str:
        """
        Hash a password using Argon2id (more secure than bcrypt).

        Args:
            password: Plain text password

        Returns:
            Argon2 hash string

        Raises:
            ValueError: If password is empty or too short
        """
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        try:
            hashed = self._password_hasher.hash(password)
            logger.debug("password_hashed_argon2")
            return hashed
        except Exception as e:
            logger.error("argon2_hash_failed", error=str(e))
            raise ValueError(f"Password hashing failed: {e}") from e

    def verify_password_argon2(self, hashed: str, password: str) -> bool:
        """
        Verify a password against an Argon2 hash.

        Args:
            hashed: Argon2 hash string
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        if not hashed or not password:
            return False

        try:
            self._password_hasher.verify(hashed, password)
            logger.debug("password_verified_argon2")
            return True
        except VerifyMismatchError:
            logger.warning("password_verification_failed", reason="mismatch")
            return False
        except InvalidHashError:
            logger.warning("password_verification_failed", reason="invalid_hash")
            return False
        except Exception as e:
            logger.error("argon2_verify_error", error=str(e))
            return False

    def check_password_needs_rehash(self, hashed: str) -> bool:
        """
        Check if a password hash needs to be rehashed (params changed).

        Args:
            hashed: Current password hash

        Returns:
            True if rehashing is recommended
        """
        try:
            return self._password_hasher.check_needs_rehash(hashed)
        except Exception:
            return True

    # ============================================
    # Input Validation & Sanitization
    # ============================================

    def sanitize_input(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize text input to prevent XSS and injection attacks.

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Truncate to max length
        sanitized = text[:max_length]

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Encode HTML special characters
        html_escape_map = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        for char, escape in html_escape_map.items():
            sanitized = sanitized.replace(char, escape)

        return sanitized

    def validate_email(self, email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid
        """
        if not email:
            return False

        # RFC 5322 simplified pattern
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def validate_uuid(self, uuid_str: str) -> bool:
        """
        Validate UUID format.

        Args:
            uuid_str: UUID string to validate

        Returns:
            True if UUID format is valid
        """
        if not uuid_str:
            return False

        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        return bool(re.match(pattern, uuid_str.lower()))

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.

        Args:
            length: Number of bytes (token will be 2x in hex)

        Returns:
            Secure random token in hexadecimal
        """
        return secrets.token_hex(length)

    # ============================================
    # Rate Limiting Helpers
    # ============================================

    def get_rate_limit_key(self, identifier: str, action: str) -> str:
        """
        Generate a rate limit key for Redis.

        Args:
            identifier: User ID or IP address
            action: Action being rate limited (e.g., 'login', 'api_call')

        Returns:
            Redis key for rate limiting
        """
        return f"rate_limit:{action}:{identifier}"


# Singleton instance
_security_service: Optional[SecurityService] = None


def get_security_service() -> SecurityService:
    """
    Get or create the security service singleton.

    Returns:
        SecurityService instance
    """
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service
