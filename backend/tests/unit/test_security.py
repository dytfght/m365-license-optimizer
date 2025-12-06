"""
Unit tests for core.security module (JWT and password hashing)
"""
from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
    verify_token_type,
)


class TestPasswordHashing:
    """Tests for password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_correct_password(self):
        """Test password verification with correct password"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test password verification with incorrect password"""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)"""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token creation and verification"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "user-id-123", "email": "user@test.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "user-id-123"}
        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        data = {"sub": "user-id-123", "email": "user@test.com"}
        token = create_access_token(data)

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "user-id-123"
        assert payload["email"] == "user@test.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_invalid_token(self):
        """Test decoding an invalid token"""
        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            decode_token(invalid_token)

    def test_token_expiration_in_payload(self):
        """Test that token has expiration time"""
        data = {"sub": "user-id-123"}
        token = create_access_token(data)
        payload = decode_token(token)

        exp = datetime.fromtimestamp(payload["exp"], timezone.utc)
        now = datetime.now(timezone.utc)

        assert exp > now  # Token should expire in the future

    def test_custom_expiration(self):
        """Test token with custom expiration"""
        data = {"sub": "user-id-123"}
        custom_expiration = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=custom_expiration)
        payload = decode_token(token)

        exp = datetime.fromtimestamp(payload["exp"], timezone.utc)
        iat = datetime.fromtimestamp(payload["iat"], timezone.utc)

        # Expiration should be approximately 5 minutes from issued time
        diff = (exp - iat).total_seconds()
        assert 290 < diff < 310  # Allow 10 seconds margin

    def test_verify_access_token_type(self):
        """Test verifying access token type"""
        data = {"sub": "user-id-123"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert verify_token_type(payload, "access") is True
        assert verify_token_type(payload, "refresh") is False

    def test_verify_refresh_token_type(self):
        """Test verifying refresh token type"""
        data = {"sub": "user-id-123"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        assert verify_token_type(payload, "refresh") is True
        assert verify_token_type(payload, "access") is False

    def test_access_token_includes_tenant_data(self):
        """Test that access token can include tenant data"""
        data = {
            "sub": "user-id-123",
            "email": "user@test.com",
            "tenants": ["tenant-id-1", "tenant-id-2"],
        }
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["sub"] == "user-id-123"
        assert payload["email"] == "user@test.com"
        assert payload["tenants"] == ["tenant-id-1", "tenant-id-2"]
