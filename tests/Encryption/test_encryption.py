"""
Unit tests for Encryption package.

Tests for MessageEncryptor, MessageDecryptor, and KeyManager.
"""

import pytest
import base64

from camouchat.Encryption import MessageEncryptor, MessageDecryptor, KeyManager


class TestKeyManager:
    """Test cases for KeyManager."""

    def test_generate_random_key(self):
        """Test that random key generation produces valid keys."""
        key = KeyManager.generate_random_key()
        assert len(key) == 32, "Key should be 32 bytes"
        assert key != KeyManager.generate_random_key(), "Random keys should be unique"

    def test_encode_decode_key(self):
        """Test key encoding and decoding."""
        key = KeyManager.generate_random_key()
        encoded = KeyManager.encode_key_for_storage(key)
        decoded = KeyManager.decode_key_from_storage(encoded)
        assert key == decoded, "Decoded key should match original"

    def test_derive_key_with_salt(self):
        """Test key derivation with provided salt."""
        key_manager = KeyManager()
        password = "test_password"
        salt, key1 = key_manager.derive_key_and_salt(password)
        key2 = key_manager.derive_key(password, salt)
        assert key1 == key2, "Same password and salt should produce same key"
        assert len(key1) == 32, "Derived key should be 32 bytes"
        assert len(salt) == 16, "Salt should be 16 bytes"

    def test_derive_key_without_salt(self):
        """Test key derivation generates random salt."""
        key_manager = KeyManager()
        password = "test_password"
        salt1, key1 = key_manager.derive_key_and_salt(password)
        salt2, key2 = key_manager.derive_key_and_salt(password)
        assert salt1 != salt2, "Different salts should be generated"
        assert key1 != key2, "Different salts should produce different keys"

    def test_empty_password_raises_error(self):
        """Test that empty password raises ValueError."""
        key_manager = KeyManager()
        with pytest.raises(ValueError):
            key_manager.derive_key_and_salt("")

    def test_invalid_salt_raises_error(self):
        """Test that invalid salt raises ValueError."""
        key_manager = KeyManager()
        with pytest.raises(ValueError):
            key_manager.derive_key("password", b"invalid_salt")

    def test_invalid_encoded_key_raises_error(self):
        """Test that invalid encoded key raises ValueError."""
        with pytest.raises(ValueError):
            KeyManager.decode_key_from_storage("not_base64!!!")


class TestMessageEncryptor:
    """Test cases for MessageEncryptor."""

    def test_init_with_invalid_key(self):
        """Test that initialization with invalid key raises ValueError."""
        with pytest.raises(ValueError):
            MessageEncryptor(b"short_key")

    def test_encrypt_string(self):
        """Test encrypting a string message."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        nonce, ciphertext = encryptor.encrypt_message("Hello, World!")
        assert len(nonce) == 12, "Nonce should be 12 bytes"
        assert len(ciphertext) > 0, "Ciphertext should not be empty"

    def test_encrypt_bytes(self):
        """Test encrypting raw bytes."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        data = b"binary_data"
        nonce, ciphertext = encryptor.encrypt_bytes(data)
        assert len(nonce) == 12, "Nonce should be 12 bytes"
        assert len(ciphertext) > 0, "Ciphertext should not be empty"

    def test_encrypt_with_message_id(self):
        """Test encrypting with message ID as associated data."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        nonce1, ciphertext1 = encryptor.encrypt_message("message", "id1")
        nonce2, ciphertext2 = encryptor.encrypt_message("message", "id2")
        # Same message with different IDs should produce different ciphertext
        assert ciphertext1 != ciphertext2, "Different IDs should produce different ciphertext"

    def test_encrypt_empty_message_raises_error(self):
        """Test that empty message raises ValueError."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        with pytest.raises(ValueError):
            encryptor.encrypt_message("")
        with pytest.raises(ValueError):
            encryptor.encrypt_bytes(b"")

    def test_nonces_are_unique(self):
        """Test that each encryption produces unique nonce."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        nonces = [encryptor.encrypt("test")[0] for _ in range(100)]
        unique_nonces = set(nonces)
        assert len(unique_nonces) == 100, "All nonces should be unique"


class TestMessageDecryptor:
    """Test cases for MessageDecryptor."""

    def test_init_with_invalid_key(self):
        """Test that initialization with invalid key raises ValueError."""
        with pytest.raises(ValueError):
            MessageDecryptor(b"short_key")

    def test_decrypt_string(self):
        """Test decrypting a string message."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        decryptor = MessageDecryptor(key)
        nonce, ciphertext = encryptor.encrypt_message("Hello, World!")
        plaintext = decryptor.decrypt_message(nonce, ciphertext)
        assert plaintext == "Hello, World!", "Decrypted text should match original"

    def test_decrypt_bytes(self):
        """Test decrypting raw bytes."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        decryptor = MessageDecryptor(key)
        data = b"binary_data"
        nonce, ciphertext = encryptor.encrypt_bytes(data)
        decrypted = decryptor.decrypt_bytes(nonce, ciphertext)
        assert decrypted == data, "Decrypted bytes should match original"

    def test_decrypt_with_wrong_key_fails(self):
        """Test that decrypting with wrong key fails."""
        key1 = KeyManager.generate_random_key()
        key2 = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key1)
        decryptor = MessageDecryptor(key2)
        nonce, ciphertext = encryptor.encrypt_message("secret")
        with pytest.raises(Exception):  # InvalidTag
            decryptor.decrypt_message(nonce, ciphertext)

    def test_decrypt_with_wrong_nonce_fails(self):
        """Test that decrypting with wrong nonce fails."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        decryptor = MessageDecryptor(key)
        nonce, ciphertext = encryptor.encrypt_message("secret")
        wrong_nonce = b"0" * 12
        with pytest.raises(Exception):  # InvalidTag
            decryptor.decrypt_message(wrong_nonce, ciphertext)

    def test_decrypt_with_modified_ciphertext_fails(self):
        """Test that decrypting modified ciphertext fails (integrity check)."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        decryptor = MessageDecryptor(key)
        nonce, ciphertext = encryptor.encrypt_message("secret")
        modified_ciphertext = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])
        with pytest.raises(Exception):  # InvalidTag
            decryptor.decrypt_message(nonce, modified_ciphertext)

    def test_decrypt_safe_returns_none_on_failure(self):
        """Test that decrypt_safe returns None on failure."""
        key = KeyManager.generate_random_key()
        encryptor = MessageEncryptor(key)
        decryptor = MessageDecryptor(key)
        nonce, ciphertext = encryptor.encrypt_message("secret")
        result = decryptor.decrypt_safe(nonce, ciphertext)
        assert result == "secret", "Valid decryption should return plaintext"
        result = decryptor.decrypt_safe(b"wrong_nonce", ciphertext)
        assert result is None, "Invalid decryption should return None"


class TestEncryptionIntegration:
    """Integration tests for encryption workflow."""

    def test_full_workflow_with_key_manager(self):
        """Test full encryption/decryption workflow with KeyManager."""
        key_manager = KeyManager()
        password = "user_password_123"
        salt, key = key_manager.derive_key_and_salt(password)

        # Encrypt message
        encryptor = MessageEncryptor(key)
        nonce, ciphertext = encryptor.encrypt_message("Secret message", "msg_123")
        encoded_ciphertext = base64.b64encode(ciphertext).decode("utf-8")
        encoded_nonce = base64.b64encode(nonce).decode("utf-8")

        # Decrypt message
        decryptor = MessageDecryptor(key)
        decoded_ciphertext = base64.b64decode(encoded_ciphertext)
        decoded_nonce = base64.b64decode(encoded_nonce)
        plaintext = decryptor.decrypt_message(decoded_nonce, decoded_ciphertext, "msg_123")

        assert plaintext == "Secret message", "Full workflow should work correctly"

    def test_multiple_messages_same_key(self):
        """Test encrypting/decrypting multiple messages with same key."""
        key_manager = KeyManager()
        salt, key = key_manager.derive_key_and_salt("password")
        encryptor = MessageEncryptor(key)
        decryptor = MessageDecryptor(key)

        messages = ["Hello", "World", "Test", "Message"]
        results = []

        for msg in messages:
            nonce, ciphertext = encryptor.encrypt_message(msg)
            plaintext = decryptor.decrypt_message(nonce, ciphertext)
            results.append(plaintext)

        assert results == messages, "All messages should be encrypted and decrypted correctly"
