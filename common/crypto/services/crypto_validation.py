"""
Crypto validation service for AK/SK validation and Bearer token handling.
"""

import base64
import hmac
import hashlib
import json
import time
from typing import Optional, Dict, Any

from ..types.crypto_types import (
    ValidationResult,
    BearerTokenPayload,
    CryptoServiceConfig,
)
from ..models.crypto_keys import CryptoKeys


class CryptoValidationService:
    """Service for validating cryptographic operations and tokens."""

    def __init__(self, config: Optional[CryptoServiceConfig] = None):
        """
        Initialize the crypto validation service.

        Args:
            config: Service configuration options
        """
        self.config = config or CryptoServiceConfig()

    def validate_ak_sk_pair(
        self, access_key: str, secret_key: str, stored_keys: CryptoKeys
    ) -> ValidationResult:
        """
        Validate an AK/SK pair against stored keys.

        Args:
            access_key: Provided access key
            secret_key: Provided secret key
            stored_keys: Stored crypto keys for the user

        Returns:
            ValidationResult indicating if AK/SK pair is valid
        """
        try:
            # Constant-time comparison to prevent timing attacks
            ak_valid = hmac.compare_digest(access_key, stored_keys.access_key)
            sk_valid = hmac.compare_digest(secret_key, stored_keys.secret_key)

            is_valid = ak_valid and sk_valid

            return ValidationResult(
                is_valid=is_valid,
                error=None if is_valid else "Invalid access key or secret key",
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False, error=f"AK/SK validation error: {str(e)}"
            )

    def create_bearer_token(self, access_key: str, secret_key: str) -> str:
        """
        Create a Bearer token for API authentication.

        Args:
            access_key: User's access key
            secret_key: User's secret key

        Returns:
            Bearer token string
        """
        timestamp = int(time.time() * 1000)  # milliseconds

        # Create payload
        payload = {"access_key": access_key, "timestamp": timestamp}

        # Create signature
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signature = self._create_signature(payload_str, secret_key)

        # Add signature to payload
        payload["signature"] = signature

        # Encode as base64
        token_str = json.dumps(payload, separators=(",", ":"))
        token_bytes = token_str.encode("utf-8")
        bearer_token = base64.b64encode(token_bytes).decode("utf-8")

        return f"Bearer {bearer_token}"

    def validate_bearer_token(
        self, bearer_token: str, stored_keys: CryptoKeys
    ) -> ValidationResult:
        """
        Validate a Bearer token.

        Args:
            bearer_token: The Bearer token to validate
            stored_keys: Stored crypto keys for validation

        Returns:
            ValidationResult indicating if token is valid
        """
        try:
            # Remove "Bearer " prefix
            if not bearer_token.startswith("Bearer "):
                return ValidationResult(
                    is_valid=False, error="Invalid Bearer token format"
                )

            token_data = bearer_token[7:]  # Remove "Bearer "

            # Decode base64
            try:
                token_bytes = base64.b64decode(token_data)
                token_str = token_bytes.decode("utf-8")
                payload = json.loads(token_str)
            except Exception:
                return ValidationResult(
                    is_valid=False, error="Invalid Bearer token encoding"
                )

            # Extract payload components
            access_key = payload.get("access_key")
            timestamp = payload.get("timestamp")
            signature = payload.get("signature")

            if not all([access_key, timestamp, signature]):
                return ValidationResult(
                    is_valid=False, error="Missing required token fields"
                )

            # Validate access key
            if not hmac.compare_digest(access_key, stored_keys.access_key):
                return ValidationResult(
                    is_valid=False, error="Invalid access key in token"
                )

            # Check token expiration
            current_time = int(time.time() * 1000)
            if current_time - timestamp > self.config.token_expiration_ms:
                return ValidationResult(
                    is_valid=False, error="Bearer token has expired"
                )

            # Validate signature
            payload_for_signature = {"access_key": access_key, "timestamp": timestamp}
            payload_str = json.dumps(
                payload_for_signature, sort_keys=True, separators=(",", ":")
            )
            expected_signature = self._create_signature(
                payload_str, stored_keys.secret_key
            )

            if not hmac.compare_digest(signature, expected_signature):
                return ValidationResult(is_valid=False, error="Invalid token signature")

            return ValidationResult(is_valid=True)

        except Exception as e:
            return ValidationResult(
                is_valid=False, error=f"Bearer token validation error: {str(e)}"
            )

    def create_content_hash(self, content: str, hash_key: str) -> str:
        """
        Create a hash of content using the provided hash key.

        Args:
            content: Content to hash
            hash_key: Base64 encoded hash key

        Returns:
            Content hash as hex string
        """
        try:
            key_bytes = base64.b64decode(hash_key.encode("utf-8"))
            content_bytes = content.encode("utf-8")

            # Create HMAC-SHA256 hash
            hash_obj = hmac.new(key_bytes, content_bytes, hashlib.sha256)
            return hash_obj.hexdigest()

        except Exception as e:
            raise ValueError(f"Content hash creation error: {str(e)}")

    def validate_content_hash(
        self, content: str, hash_key: str, expected_hash: str
    ) -> ValidationResult:
        """
        Validate a content hash.

        Args:
            content: Original content
            hash_key: Base64 encoded hash key
            expected_hash: Expected hash value

        Returns:
            ValidationResult indicating if hash is valid
        """
        try:
            actual_hash = self.create_content_hash(content, hash_key)

            is_valid = hmac.compare_digest(actual_hash, expected_hash)

            return ValidationResult(
                is_valid=is_valid,
                error=None if is_valid else "Content hash validation failed",
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False, error=f"Content hash validation error: {str(e)}"
            )

    def _create_signature(self, payload: str, secret_key: str) -> str:
        """
        Create HMAC signature for payload.

        Args:
            payload: JSON payload string
            secret_key: Base64 encoded secret key

        Returns:
            Base64 encoded signature
        """
        key_bytes = base64.b64decode(secret_key.encode("utf-8"))
        payload_bytes = payload.encode("utf-8")

        signature_bytes = hmac.new(key_bytes, payload_bytes, hashlib.sha256).digest()
        return base64.b64encode(signature_bytes).decode("utf-8")

    def parse_bearer_token(self, bearer_token: str) -> Optional[BearerTokenPayload]:
        """
        Parse a Bearer token and return its payload (without validation).

        Args:
            bearer_token: The Bearer token to parse

        Returns:
            BearerTokenPayload if parsing successful, None otherwise
        """
        try:
            if not bearer_token.startswith("Bearer "):
                return None

            token_data = bearer_token[7:]
            token_bytes = base64.b64decode(token_data)
            token_str = token_bytes.decode("utf-8")
            payload = json.loads(token_str)

            return BearerTokenPayload(
                access_key=payload.get("access_key", ""),
                timestamp=payload.get("timestamp", 0),
                signature=payload.get("signature", ""),
            )

        except Exception:
            return None
