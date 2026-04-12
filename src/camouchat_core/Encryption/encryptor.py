"""
Encryption module for platform messages using AES-256-GCM.

Provides secure encryption with authenticated encryption (AEAD) to ensure
both confidentiality and integrity of stored messages.
"""

from __future__ import annotations

import os
from typing import Tuple, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class MessageEncryptor:
    """
    Handles encryption of platform messages using AES-256-GCM.

    AES-256-GCM provides:
    - 256-bit encryption key (32 bytes)
    - Authenticated encryption with additional data
    - Built-in integrity verification via authentication tag

    Security properties:
    - Never reuse nonce with the same key
    - Nonce must be 12 bytes (96 bits) for GCM
    - Authentication tag automatically appended to ciphertext
    """

    def __init__(self, key: bytes) -> None:
        """
        Initialize encryptor with encryption key.

        Args:
            key: 32-byte (256-bit) encryption key

        Raises:
            ValueError: If key is not 32 bytes
        """
        if len(key) != 32:
            raise ValueError(f"Key must be 32 bytes (256 bits), got {len(key)} bytes")

        self.key = key
        self.aesgcm = AESGCM(key)

    def encrypt(
        self, plaintext: str | bytes, associated_data: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """
        Encrypt plaintext using AES-256-GCM.

        Args:
            plaintext: Message to encrypt (string or bytes)
            associated_data: Optional additional authenticated data (AA)
                          Data that is authenticated but not encrypted (e.g., metadata)

        Returns:
            Tuple of (nonce, ciphertext):
            - nonce: 12-byte nonce used for encryption
            - ciphertext: Encrypted data with authentication tag appended

        Raises:
            ValueError: If plaintext is empty after encoding
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        if not plaintext:
            raise ValueError("Plaintext cannot be empty")

        # Generate random 96-bit nonce (12 bytes)
        nonce = os.urandom(12)

        # Encrypt with AES-256-GCM
        # The authentication tag is automatically appended to ciphertext
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, associated_data)

        return nonce, ciphertext

    def encrypt_message(
        self, message: str, message_id: Optional[str] = None
    ) -> Tuple[bytes, bytes]:
        """
        Encrypt a message with optional ID as associated data.

        Args:
            message: Message text to encrypt
            message_id: Optional message ID to authenticate (not encrypt)

        Returns:
            Tuple of (nonce, ciphertext)
        """
        associated_data = message_id.encode("utf-8") if message_id else None
        return self.encrypt(message, associated_data)

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a random 256-bit encryption key.

        Returns:
            32-byte random key suitable for AES-256

        Note:
            This key should be stored securely and used consistently
            for the same user to enable decryption of their messages.
        """
        return AESGCM.generate_key(bit_length=256)

    def encrypt_bytes(
        self, data: bytes, associated_data: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """
        Encrypt raw bytes using AES-256-GCM.

        Args:
            data: Raw bytes to encrypt
            associated_data: Optional additional authenticated data

        Returns:
            Tuple of (nonce, ciphertext)
        """
        if not data:
            raise ValueError("Data cannot be empty")

        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, data, associated_data)

        return nonce, ciphertext
