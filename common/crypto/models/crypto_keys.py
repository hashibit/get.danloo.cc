"""
Crypto Keys data model for managing user encryption keys.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CryptoKeys:
    """
    Data model for storing user cryptographic keys and authentication data.

    Attributes:
        user_id: Unique identifier for the user
        access_key: Public access key (AK) for API authentication
        secret_key: Private secret key (SK) for API authentication
        hash_key: Random key for content hashing operations
        salt: Random salt for password hashing
        password_hash: Hashed password (optional, may be stored separately)
        created_at: Timestamp when keys were created
        updated_at: Timestamp when keys were last updated
    """

    user_id: str
    access_key: str
    secret_key: str
    hash_key: str
    salt: str
    password_hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert the CryptoKeys instance to a dictionary."""
        return {
            "user_id": self.user_id,
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "hash_key": self.hash_key,
            "salt": self.salt,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CryptoKeys":
        """Create a CryptoKeys instance from a dictionary."""
        created_at = None
        updated_at = None

        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            user_id=data["user_id"],
            access_key=data["access_key"],
            secret_key=data["secret_key"],
            hash_key=data["hash_key"],
            salt=data["salt"],
            password_hash=data.get("password_hash"),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
        )
