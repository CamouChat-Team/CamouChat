"""
Key management module for platform message encryption.

Handles key derivation from user passwords using PBKDF2-HMAC,
a secure key derivation function with configurable iterations.
"""

from __future__ import annotations

import os
import base64
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class KeyManager:
    """
    Manages encryption key derivation using PBKDF2-HMAC.

    PBKDF2-HMAC provides:
    - Secure key derivation from passwords
    - Configurable iterations for security vs performance trade-off
    - Resistance to brute-force attacks with high iteration counts

    Security properties:
    - Each user has a unique salt
    - Keys are derived from user passwords
    - Same password + salt always produces same key
    """

    def __init__(self, iterations: int = 480000) -> None:
        """
        Initialize key manager with PBKDF2 parameters.

        Args:
            iterations: Number of iterations (default: 480000, recommended by OWASP)
                       Higher values increase security but slow down key derivation.

        Note:
            480000 iterations is OWASP recommended for PBKDF2-HMAC-SHA256.
            Adjust based on your security requirements and performance needs.
        """
        self.iterations = iterations

    def derive_key_and_salt(
        self, password: str, salt: Optional[bytes] = None
    ) -> tuple[bytes, bytes]:
        """
        Derive an encryption key from password using PBKDF2-HMAC.

        Args:
            password: User password
            salt: Optional 16-byte salt. If None, generates a random salt.

        Returns:
            Tuple of (salt, key):
            - salt: 16-byte salt used for key derivation
            - key: 32-byte derived encryption key

        Raises:
            ValueError: If password is empty
        """
        if not password:
            raise ValueError("Password cannot be empty")

        # Generate random salt if not provided
        if salt is None:
            salt = os.urandom(16)

        if len(salt) != 16:
            raise ValueError(f"Salt must be 16 bytes, got {len(salt)} bytes")

        # Convert password to bytes
        password_bytes = password.encode("utf-8")

        # Create PBKDF2-HMAC-SHA256 KDF instance
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key for AES-256
            salt=salt,
            iterations=self.iterations,
        )

        # Derive key
        key = kdf.derive(password_bytes)

        return salt, key

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive an encryption key from password and existing salt.

        Args:
            password: User password
            salt: 16-byte salt used during original key derivation

        Returns:
            32-byte derived encryption key

        Raises:
            ValueError: If password is empty or salt is not 16 bytes
        """
        _, key = self.derive_key_and_salt(password, salt)
        return key

    @staticmethod
    def generate_random_key() -> bytes:
        """
        Generate a random 32-byte encryption key.

        Returns:
            32-byte random key

        Note:
            This is an alternative to password-based keys.
            Random keys must be stored securely by the application.
        """
        return os.urandom(32)

    @staticmethod
    def encode_key_for_storage(key: bytes) -> str:
        """
        Encode a key for safe storage.

        Args:
            key: Raw 32-byte key

        Returns:
            Base64-encoded key string

        Note:
            Encoded keys can be stored in config files or databases.
            Never store raw keys or passwords in plaintext.
        """
        return base64.b64encode(key).decode("utf-8")

    @staticmethod
    def decode_key_from_storage(encoded_key: str) -> bytes:
        """
        Decode a key from storage format.

        Args:
            encoded_key: Base64-encoded key string

        Returns:
            Raw 32-byte key

        Raises:
            ValueError: If encoded_key is invalid
        """
        try:
            return base64.b64decode(encoded_key.encode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decode key: {e}") from e
