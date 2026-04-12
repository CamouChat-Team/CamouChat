"""
Encryption package for camouchat SDK.

Provides secure encryption and decryption for platform messages using:
- AES-256-GCM for authenticated encryption
- PBKDF2-HMAC-SHA256 for key derivation (480,000 iterations, OWASP recommended)
- Per-user encryption keys

Usage:
    from camouchat.Encryption import MessageEncryptor, MessageDecryptor, KeyManager

    # Generate key from password
    key_manager = KeyManager()
    salt, key = key_manager.derive_key_and_salt("user_password")

    # Encrypt message
    encryptor = MessageEncryptor(key)
    nonce, ciphertext = encryptor.encrypt_message("Hello, World!")

    # Decrypt message
    decryptor = MessageDecryptor(key)
    plaintext = decryptor.decrypt_message(nonce, ciphertext)
"""

from .encryptor import MessageEncryptor
from .decryptor import MessageDecryptor
from .key_manager import KeyManager

__all__ = [
    "MessageEncryptor",
    "MessageDecryptor",
    "KeyManager",
]
