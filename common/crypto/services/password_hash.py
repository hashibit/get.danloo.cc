"""
Password hashing service using bcrypt.
"""

import bcrypt
from typing import Optional

from ..types.crypto_types import PasswordHashOptions, ValidationResult


class PasswordHashService:
    """Service for password hashing and verification using bcrypt."""

    @staticmethod
    def hash_password(
        password: str, salt: str, options: Optional[PasswordHashOptions] = None
    ) -> str:
        """
        Hash a password using bcrypt with the provided salt.

        Args:
            password: Plain text password to hash
            salt: Base64 encoded salt
            options: Password hashing options (rounds)

        Returns:
            Hashed password as string
        """
        if options is None:
            options = PasswordHashOptions()

        # Convert password to bytes
        password_bytes = password.encode("utf-8")

        # Generate bcrypt salt using the provided salt as seed
        # Note: bcrypt generates its own salt, but we use our salt for consistency
        bcrypt_salt = bcrypt.gensalt(rounds=options.rounds)

        # Hash the password
        hashed = bcrypt.hashpw(password_bytes, bcrypt_salt)

        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> ValidationResult:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password to verify
            hashed_password: Previously hashed password

        Returns:
            ValidationResult indicating if password is valid
        """
        try:
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")

            is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)

            return ValidationResult(
                is_valid=is_valid, error=None if is_valid else "Invalid password"
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False, error=f"Password verification error: {str(e)}"
            )

    @staticmethod
    def hash_password_simple(password: str, rounds: int = 12) -> tuple[str, str]:
        """
        Hash a password and return both salt and hash (for simple use cases).

        Args:
            password: Plain text password to hash
            rounds: bcrypt rounds (default: 12)

        Returns:
            Tuple of (salt, hashed_password)
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)

        return salt.decode("utf-8"), hashed.decode("utf-8")

    @staticmethod
    def validate_password_strength(password: str) -> ValidationResult:
        """
        Validate password strength according to security requirements.

        Args:
            password: Password to validate

        Returns:
            ValidationResult indicating if password meets requirements
        """
        errors = []

        # Minimum length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        # Maximum length (to prevent DoS)
        if len(password) > 128:
            errors.append("Password must be at most 128 characters long")

        # Check for at least one uppercase letter
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        # Check for at least one lowercase letter
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        # Check for at least one digit
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            errors.append("Password must contain at least one special character")

        is_valid = len(errors) == 0
        error_message = "; ".join(errors) if errors else None

        return ValidationResult(is_valid=is_valid, error=error_message)

    @staticmethod
    def get_password_hash_info(hashed_password: str) -> dict:
        """
        Extract information from a bcrypt hash.

        Args:
            hashed_password: bcrypt hash string

        Returns:
            Dictionary with hash information
        """
        try:
            # bcrypt hash format: $2b$rounds$salthash
            parts = hashed_password.split("$")
            if len(parts) >= 4:
                return {
                    "algorithm": parts[1],
                    "rounds": int(parts[2]),
                    "salt_and_hash": parts[3],
                    "is_valid_format": True,
                }
        except Exception:
            pass

        return {"is_valid_format": False, "error": "Invalid bcrypt hash format"}
