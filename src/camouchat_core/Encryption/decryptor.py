"""
Decryption module for platform messages using AES-256-GCM.

Handles decryption of encrypted messages with authentication tag verification
to ensure data integrity and authenticity.
"""

from __future__ import annotations

from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class MessageDecryptor:
    """
    Handles decryption of platform messages using AES-256-GCM.

    Decryption process automatically verifies the authentication tag,
    ensuring the message has not been tampered with or corrupted.

    Security properties:
    - Authentication tag verification is automatic
    - Decryption fails if tag is invalid or ciphertext modified
    - Must use same key and nonce as encryption
    """

    def __init__(self, key: bytes) -> None:
        """
        Initialize decryptor with decryption key.

        Args:
            key: 32-byte (256-bit) decryption key (same as encryption key)

        Raises:
            ValueError: If key is not 32 bytes
        """
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes (256 bits), got {len(key)} bytes")

        self.key = key
        self.aesgcm = AESGCM(key)

    def decrypt(
        self, nonce: bytes, ciphertext: bytes, associated_data: Optional[bytes] = None
    ) -> str:
        """
        Decrypt ciphertext using AES-256-GCM.

        Args:
            nonce: 12-byte nonce used during encryption
            ciphertext: Encrypted data with authentication tag appended
            associated_data: Optional additional authenticated data
                          Must match the data used during encryption

        Returns:
            Decrypted plaintext as UTF-8 string

        Raises:
            InvalidTag: If authentication tag verification fails
                        (message corrupted or tampered with)
            ValueError: If nonce is not 12 bytes or ciphertext is empty
        """
        if len(nonce) != 12:
            raise ValueError(f"Nonce must be 12 bytes, got {len(nonce)} bytes")

        if not ciphertext:
            raise ValueError("Ciphertext cannot be empty")

        # Decrypt with automatic authentication tag verification
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, associated_data)

        return plaintext.decode("utf-8")

    def decrypt_message(
        self, nonce: bytes, ciphertext: bytes, message_id: Optional[str] = None
    ) -> str:
        """
        Decrypt a message with optional ID as associated data.

        Args:
            nonce: 12-byte nonce used during encryption
            ciphertext: Encrypted message data
            message_id: Optional message ID used during encryption

        Returns:
            Decrypted message text

        Raises:
            InvalidTag: If authentication fails
        """
        associated_data = message_id.encode("utf-8") if message_id else None
        return self.decrypt(nonce, ciphertext, associated_data)

    def decrypt_bytes(
        self, nonce: bytes, ciphertext: bytes, associated_data: Optional[bytes] = None
    ) -> bytes:
        """
        Decrypt raw bytes using AES-256-GCM.

        Args:
            nonce: 12-byte nonce used during encryption
            ciphertext: Encrypted data with authentication tag
            associated_data: Optional additional authenticated data

        Returns:
            Decrypted raw bytes

        Raises:
            InvalidTag: If authentication tag verification fails
            ValueError: If nonce is not 12 bytes or ciphertext is empty
        """
        if len(nonce) != 12:
            raise ValueError(f"Nonce must be 12 bytes, got {len(nonce)} bytes")

        if not ciphertext:
            raise ValueError("Ciphertext cannot be empty")

        # Decrypt with automatic authentication tag verification
        return self.aesgcm.decrypt(nonce, ciphertext, associated_data)

    def decrypt_safe(
        self, nonce: bytes, ciphertext: bytes, associated_data: Optional[bytes] = None
    ) -> Optional[str]:
        """
        Safely decrypt with error handling.

        Args:
            nonce: 12-byte nonce used during encryption
            ciphertext: Encrypted data with authentication tag
            associated_data: Optional additional authenticated data

        Returns:
            Decrypted plaintext as string, or None if decryption fails

        Note:
            This method catches InvalidTag and returns None instead of raising.
            Useful for scenarios where you want to handle decryption failures gracefully.
        """
        try:
            return self.decrypt(nonce, ciphertext, associated_data)
        except (InvalidTag, ValueError):
            return None
