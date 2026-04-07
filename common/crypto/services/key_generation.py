"""
Key generation service for creating cryptographic keys.
"""

import secrets
import base64
import hashlib
from typing import Optional

from ..types.crypto_types import KeyPair, KeyGenerationOptions, EncodingType


class KeyGenerationService:
    """Service for generating cryptographic keys."""

    @staticmethod
    def generate_key_pair(options: Optional[KeyGenerationOptions] = None) -> KeyPair:
        """
        Generate an access key and secret key pair.

        Args:
            options: Key generation options (length, encoding)

        Returns:
            KeyPair with access_key and secret_key
        """
        if options is None:
            options = KeyGenerationOptions()

        access_key = KeyGenerationService._generate_random_key(options)
        secret_key = KeyGenerationService._generate_random_key(options)

        return KeyPair(access_key=access_key, secret_key=secret_key)

    @staticmethod
    def generate_hash_key(options: Optional[KeyGenerationOptions] = None) -> str:
        """
        Generate a random hash key for content hashing.

        Args:
            options: Key generation options (length, encoding)

        Returns:
            Random hash key as encoded string
        """
        if options is None:
            options = KeyGenerationOptions()

        return KeyGenerationService._generate_random_key(options)

    @staticmethod
    def generate_salt(
        length: int = 16, encoding: EncodingType = EncodingType.BASE64
    ) -> str:
        """
        Generate a random salt for password hashing.

        Args:
            length: Length in bytes (default: 16)
            encoding: Encoding type (default: base64)

        Returns:
            Random salt as encoded string
        """
        options = KeyGenerationOptions(key_length=length, encoding=encoding)
        return KeyGenerationService._generate_random_key(options)

    @staticmethod
    def _generate_random_key(options: KeyGenerationOptions) -> str:
        """
        Generate a cryptographically secure random key.

        Args:
            options: Key generation options

        Returns:
            Random key as encoded string
        """
        # Generate cryptographically secure random bytes
        random_bytes = secrets.token_bytes(options.key_length)

        # Encode based on the specified encoding
        if options.encoding == EncodingType.BASE64:
            return base64.b64encode(random_bytes).decode("utf-8")
        elif options.encoding == EncodingType.HEX:
            return random_bytes.hex()
        else:
            raise ValueError(f"Unsupported encoding type: {options.encoding}")

    @staticmethod
    def derive_key_from_password(password: str, salt: str, key_length: int = 32) -> str:
        """
        Derive a key from password using PBKDF2.

        Args:
            password: The password to derive from
            salt: Salt as base64 string
            key_length: Length of derived key in bytes

        Returns:
            Derived key as base64 string
        """
        salt_bytes = base64.b64decode(salt.encode("utf-8"))
        derived_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt_bytes,
            100000,  # iterations
            key_length,
        )
        return base64.b64encode(derived_key).decode("utf-8")

    @staticmethod
    def validate_key_format(
        key: str, encoding: EncodingType = EncodingType.BASE64
    ) -> bool:
        """
        Validate if a key has the correct format.

        Args:
            key: The key to validate
            encoding: Expected encoding type

        Returns:
            True if key format is valid
        """
        try:
            if encoding == EncodingType.BASE64:
                base64.b64decode(key)
                return True
            elif encoding == EncodingType.HEX:
                bytes.fromhex(key)
                return True
            else:
                return False
        except Exception:
            return False
