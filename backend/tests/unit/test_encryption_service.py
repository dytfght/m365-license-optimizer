"""
Unit tests for encryption_service (LOT4)
"""
import pytest
from cryptography.fernet import Fernet

from src.services.encryption_service import EncryptionService


@pytest.mark.unit
class TestEncryptionService:
    """Tests for EncryptionService"""

    def test_initialization_with_valid_key(self):
        """Test service initialization with valid Fernet key"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        assert service is not None
        assert service._fernet is not None

    def test_initialization_with_invalid_key(self):
        """Test service initialization with invalid key"""
        with pytest.raises(ValueError, match="Invalid encryption key"):
            EncryptionService("invalid-key-format")

    def test_encrypt_decrypt_round_trip(self):
        """Test encrypt/decrypt round trip"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        original_text = "my-super-secret-client-secret"
        encrypted = service.encrypt(original_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original_text
        assert encrypted != original_text  # Ensure it was actually encrypted
        assert isinstance(encrypted, str)

    def test_encrypt_empty_string(self):
        """Test encrypting empty string raises error"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        with pytest.raises(ValueError, match="Cannot encrypt empty string"):
            service.encrypt("")

    def test_encrypt_unicode_characters(self):
        """Test encrypting text with unicode characters"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        original_text = "Clé secrète avec des accents: é è à ç 中文"
        encrypted = service.encrypt(original_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original_text

    def test_encrypt_long_text(self):
        """Test encrypting long text"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        original_text = "A" * 10000  # 10KB text
        encrypted = service.encrypt(original_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original_text

    def test_decrypt_with_wrong_key(self):
        """Test decryption with wrong key fails"""
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        service1 = EncryptionService(key1)
        service2 = EncryptionService(key2)

        encrypted = service1.encrypt("secret")

        with pytest.raises(ValueError, match="Decryption failed"):
            service2.decrypt(encrypted)

    def test_decrypt_invalid_token(self):
        """Test decryption of invalid encrypted data"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        with pytest.raises(ValueError, match="Decryption failed"):
            service.decrypt("not-valid-encrypted-data")

    def test_encrypt_none_value(self):
        """Test encrypting None value raises error"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        with pytest.raises(ValueError, match="Cannot encrypt empty string"):
            service.encrypt(None)

    def test_decrypt_none_value(self):
        """Test decrypting None value raises error"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        with pytest.raises(ValueError, match="Cannot decrypt empty string"):
            service.decrypt(None)

    def test_different_encryptions_same_plaintext(self):
        """Test that same plaintext produces different ciphertexts (timestamp-based)"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        original_text = "secret-data"
        encrypted1 = service.encrypt(original_text)
        encrypted2 = service.encrypt(original_text)

        # Fernet includes timestamp, so same plaintext should produce different ciphertexts
        assert encrypted1 != encrypted2
        # But both should decrypt to same plaintext
        assert service.decrypt(encrypted1) == original_text
        assert service.decrypt(encrypted2) == original_text

    def test_encrypt_special_characters(self):
        """Test encrypting text with special characters"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        original_text = "!@#$%^&*()_+-=[]{}|;':,.<>?/~`"
        encrypted = service.encrypt(original_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original_text

    def test_encrypt_json_string(self):
        """Test encrypting JSON-like string"""
        key = Fernet.generate_key().decode()
        service = EncryptionService(key)

        original_text = '{"client_id": "123", "client_secret": "abc"}'
        encrypted = service.encrypt(original_text)
        decrypted = service.decrypt(encrypted)

        assert decrypted == original_text
