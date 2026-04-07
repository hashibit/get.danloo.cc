"""
Type definitions for the crypto module.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal
from enum import Enum


class EncodingType(str, Enum):
    BASE64 = "base64"
    HEX = "hex"


@dataclass
class KeyPair:
    access_key: str
    secret_key: str


@dataclass
class KeyGenerationOptions:
    key_length: int = 32  # bytes
    encoding: EncodingType = EncodingType.BASE64


@dataclass
class PasswordHashOptions:
    rounds: int = 12  # bcrypt rounds


@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None


@dataclass
class BearerTokenPayload:
    access_key: str
    timestamp: int
    signature: str


@dataclass
class CryptoServiceConfig:
    default_key_length: int = 32
    default_encoding: EncodingType = EncodingType.BASE64
    bcrypt_rounds: int = 12
    token_expiration_ms: int = 300000  # 5 minutes
