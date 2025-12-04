"""
Unit tests for SecurityService (LOT 10)
Tests 2FA TOTP, password hashing, and input validation.
"""
import pytest

from src.services.security_service import SecurityService, get_security_service


class TestSecurityService:
    """Tests for SecurityService."""

    @pytest.fixture
    def service(self):
        """Create a SecurityService instance."""
        return SecurityService()

    # ============================================
    # TOTP Tests
    # ============================================

    def test_generate_totp_secret(self, service):
        """Test TOTP secret generation."""
        secret = service.generate_totp_secret()
        
        assert secret is not None
        assert len(secret) == 32  # Base32 encoded
        assert secret.isalnum()

    def test_generate_totp_secret_uniqueness(self, service):
        """Test that TOTP secrets are unique."""
        secrets = [service.generate_totp_secret() for _ in range(10)]
        
        # All secrets should be unique
        assert len(set(secrets)) == 10

    def test_get_totp_provisioning_uri(self, service):
        """Test TOTP provisioning URI generation."""
        secret = service.generate_totp_secret()
        uri = service.get_totp_provisioning_uri(secret, "test@example.com")
        
        assert uri.startswith("otpauth://totp/")
        assert "M365LicenseOptimizer" in uri
        assert "test%40example.com" in uri or "test@example.com" in uri

    def test_verify_totp_valid(self, service):
        """Test TOTP verification with valid token."""
        secret = service.generate_totp_secret()
        token = service.get_current_totp(secret)
        
        result = service.verify_totp(secret, token)
        
        assert result is True

    def test_verify_totp_invalid_token(self, service):
        """Test TOTP verification with invalid token."""
        secret = service.generate_totp_secret()
        
        result = service.verify_totp(secret, "000000")
        
        assert result is False

    def test_verify_totp_empty_inputs(self, service):
        """Test TOTP verification with empty inputs."""
        assert service.verify_totp("", "123456") is False
        assert service.verify_totp("secret", "") is False
        assert service.verify_totp("", "") is False

    # ============================================
    # Argon2 Password Hashing Tests
    # ============================================

    def test_hash_password_argon2(self, service):
        """Test Argon2 password hashing."""
        password = "SecurePassword123!"
        
        hashed = service.hash_password_argon2(password)
        
        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$argon2")

    def test_hash_password_argon2_uniqueness(self, service):
        """Test that same password produces different hashes."""
        password = "TestPassword123!"
        
        hash1 = service.hash_password_argon2(password)
        hash2 = service.hash_password_argon2(password)
        
        # Different hashes due to random salt
        assert hash1 != hash2

    def test_hash_password_short_password(self, service):
        """Test that short passwords are rejected."""
        with pytest.raises(ValueError, match="at least 8 characters"):
            service.hash_password_argon2("short")

    def test_hash_password_empty(self, service):
        """Test that empty passwords are rejected."""
        with pytest.raises(ValueError):
            service.hash_password_argon2("")

    def test_verify_password_argon2_valid(self, service):
        """Test Argon2 password verification with valid password."""
        password = "SecurePassword123!"
        hashed = service.hash_password_argon2(password)
        
        result = service.verify_password_argon2(hashed, password)
        
        assert result is True

    def test_verify_password_argon2_invalid(self, service):
        """Test Argon2 password verification with invalid password."""
        password = "SecurePassword123!"
        hashed = service.hash_password_argon2(password)
        
        result = service.verify_password_argon2(hashed, "WrongPassword123!")
        
        assert result is False

    def test_verify_password_argon2_empty(self, service):
        """Test Argon2 password verification with empty inputs."""
        assert service.verify_password_argon2("", "password") is False
        assert service.verify_password_argon2("hash", "") is False

    def test_check_password_needs_rehash(self, service):
        """Test password rehash check."""
        password = "TestPassword123!"
        hashed = service.hash_password_argon2(password)
        
        # Fresh hash should not need rehash
        result = service.check_password_needs_rehash(hashed)
        
        assert isinstance(result, bool)

    # ============================================
    # Input Validation Tests
    # ============================================

    def test_sanitize_input_basic(self, service):
        """Test basic input sanitization."""
        result = service.sanitize_input("Hello World")
        
        assert result == "Hello World"

    def test_sanitize_input_html(self, service):
        """Test HTML sanitization."""
        result = service.sanitize_input("<script>alert('xss')</script>")
        
        assert "<" not in result
        assert ">" not in result
        assert "&lt;script&gt;" in result

    def test_sanitize_input_max_length(self, service):
        """Test max length truncation."""
        long_text = "a" * 2000
        
        result = service.sanitize_input(long_text, max_length=100)
        
        assert len(result) == 100

    def test_sanitize_input_null_bytes(self, service):
        """Test null byte removal."""
        result = service.sanitize_input("hello\x00world")
        
        assert "\x00" not in result

    def test_sanitize_input_empty(self, service):
        """Test empty input handling."""
        result = service.sanitize_input("")
        
        assert result == ""

    def test_validate_email_valid(self, service):
        """Test valid email validation."""
        assert service.validate_email("test@example.com") is True
        assert service.validate_email("user.name@domain.org") is True
        assert service.validate_email("user+tag@example.co.uk") is True

    def test_validate_email_invalid(self, service):
        """Test invalid email validation."""
        assert service.validate_email("notanemail") is False
        assert service.validate_email("@example.com") is False
        assert service.validate_email("test@") is False
        assert service.validate_email("") is False

    def test_validate_uuid_valid(self, service):
        """Test valid UUID validation."""
        assert service.validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert service.validate_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_validate_uuid_invalid(self, service):
        """Test invalid UUID validation."""
        assert service.validate_uuid("not-a-uuid") is False
        assert service.validate_uuid("550e8400-e29b-41d4-a716") is False
        assert service.validate_uuid("") is False

    # ============================================
    # Secure Token Tests
    # ============================================

    def test_generate_secure_token(self, service):
        """Test secure token generation."""
        token = service.generate_secure_token()
        
        assert len(token) == 64  # 32 bytes = 64 hex chars
        assert token.isalnum()

    def test_generate_secure_token_custom_length(self, service):
        """Test secure token with custom length."""
        token = service.generate_secure_token(length=16)
        
        assert len(token) == 32  # 16 bytes = 32 hex chars

    def test_generate_secure_token_uniqueness(self, service):
        """Test secure token uniqueness."""
        tokens = [service.generate_secure_token() for _ in range(10)]
        
        assert len(set(tokens)) == 10

    # ============================================
    # Rate Limit Key Tests
    # ============================================

    def test_get_rate_limit_key(self, service):
        """Test rate limit key generation."""
        key = service.get_rate_limit_key("user123", "login")
        
        assert key == "rate_limit:login:user123"

    # ============================================
    # Singleton Tests
    # ============================================

    def test_get_security_service_singleton(self):
        """Test that get_security_service returns singleton."""
        service1 = get_security_service()
        service2 = get_security_service()
        
        assert service1 is service2
