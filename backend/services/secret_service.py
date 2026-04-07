"""
Secret service for managing user encryption keys and authentication.
"""

from sqlalchemy.orm import Session
from common.database_models.crypto_keys_model import CryptoKeysDB
from common.database_models.user_model import UserDB
from common.crypto import (
    CryptoKeys,
    KeyGenerationService,
    PasswordHashService,
    CryptoValidationService,
)

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SecretService:
    """Service for managing user secret keys and authentication."""

    def __init__(self):
        """Initialize crypto service with configuration."""
        self.key_gen_service = KeyGenerationService()
        self.password_service = PasswordHashService()
        self.validation_service = CryptoValidationService()

    def create_user_crypto_keys(self, db: Session, user_id: str) -> CryptoKeysDB:
        """
        Create crypto keys for a new user.

        Args:
            db: Database session
            user_id: User ID to create keys for

        Returns:
            Created CryptoKeysDB record
        """
        try:
            # Check if crypto keys already exist for this user
            existing_keys = (
                db.query(CryptoKeysDB).filter(CryptoKeysDB.user_id == user_id).first()
            )
            if existing_keys:
                raise ValueError(f"Crypto keys already exist for user {user_id}")

            # Generate new crypto keys
            key_pair = self.key_gen_service.generate_key_pair()
            hash_key = self.key_gen_service.generate_hash_key()
            salt = self.key_gen_service.generate_salt()

            # Create database record
            crypto_keys_db = CryptoKeysDB(
                user_id=user_id,
                access_key=key_pair.access_key,
                secret_key=key_pair.secret_key,
                hash_key=hash_key,
                salt=salt,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            db.add(crypto_keys_db)
            db.commit()
            db.refresh(crypto_keys_db)

            logger.info(f"Created crypto keys for user {user_id}")
            return crypto_keys_db

        except Exception as e:
            logger.error(f"Failed to create crypto keys for user {user_id}: {str(e)}")
            db.rollback()
            raise

    def get_user_crypto_keys(self, db: Session, user_id: str) -> CryptoKeysDB | None:
        """
        Get crypto keys for a user.

        Args:
            db: Database session
            user_id: User ID to get keys for

        Returns:
            CryptoKeysDB record or None
        """
        return db.query(CryptoKeysDB).filter(CryptoKeysDB.user_id == user_id).first()

    def get_user_by_access_key(self, db: Session, access_key: str) -> UserDB | None:
        """
        Get user by access key.

        Args:
            db: Database session
            access_key: Access key to search for

        Returns:
            UserDB record or None
        """
        crypto_keys = (
            db.query(CryptoKeysDB).filter(CryptoKeysDB.access_key == access_key).first()
        )
        if crypto_keys:
            return db.query(UserDB).filter(UserDB.id == crypto_keys.user_id).first()
        return None

    def create_bearer_token_for_ai_provider(self, db: Session, user_id: str) -> str:
        """
        Create Bearer token for accessing ai-provider services.

        Args:
            db: Database session
            user_id: User ID to create token for

        Returns:
            Bearer token string
        """
        crypto_keys = self.get_user_crypto_keys(db, user_id)
        if not crypto_keys:
            raise ValueError(f"No crypto keys found for user {user_id}")

        try:
            bearer_token = self.validation_service.create_bearer_token(
                crypto_keys.access_key, crypto_keys.secret_key
            )

            logger.info(f"Created Bearer token for user {user_id}")
            return bearer_token

        except Exception as e:
            logger.error(f"Failed to create Bearer token for user {user_id}: {str(e)}")
            raise

    def validate_ak_sk_pair(
        self, db: Session, access_key: str, secret_key: str
    ) -> bool:
        """
        Validate AK/SK pair against stored keys.

        Args:
            db: Database session
            access_key: Access key to validate
            secret_key: Secret key to validate

        Returns:
            True if valid, False otherwise
        """
        crypto_keys = (
            db.query(CryptoKeysDB).filter(CryptoKeysDB.access_key == access_key).first()
        )
        if not crypto_keys:
            return False

        # Convert to CryptoKeys model for validation
        stored_keys = CryptoKeys(
            user_id=crypto_keys.user_id,
            access_key=crypto_keys.access_key,
            secret_key=crypto_keys.secret_key,
            hash_key=crypto_keys.hash_key,
            salt=crypto_keys.salt,
            created_at=crypto_keys.created_at,
            updated_at=crypto_keys.updated_at,
        )

        result = self.validation_service.validate_ak_sk_pair(
            access_key, secret_key, stored_keys
        )
        return result.is_valid

    def update_user_password_hash(
        self, db: Session, user_id: str, new_password: str
    ) -> bool:
        """
        Update user's password hash using their salt.

        Args:
            db: Database session
            user_id: User ID
            new_password: New password to hash

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user's crypto keys for salt
            crypto_keys = self.get_user_crypto_keys(db, user_id)
            if not crypto_keys:
                raise ValueError(f"No crypto keys found for user {user_id}")

            # Hash the new password
            hashed_password = self.password_service.hash_password(
                new_password, crypto_keys.salt
            )

            # Update user's password hash
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            user.password_hash = hashed_password
            user.updated_at = datetime.now()

            db.commit()

            logger.info(f"Updated password hash for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update password hash for user {user_id}: {str(e)}")
            db.rollback()
            return False

    def verify_user_password(self, db: Session, user_id: str, password: str) -> bool:
        """
        Verify user's password against stored hash.

        Args:
            db: Database session
            user_id: User ID
            password: Password to verify

        Returns:
            True if password is correct, False otherwise
        """
        try:
            user = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user:
                return False

            result = self.password_service.verify_password(password, user.password_hash)
            return result.is_valid

        except Exception as e:
            logger.error(f"Failed to verify password for user {user_id}: {str(e)}")
            return False

    def rotate_user_keys(self, db: Session, user_id: str) -> CryptoKeysDB:
        """
        Rotate user's crypto keys (generate new AK/SK pair).

        Args:
            db: Database session
            user_id: User ID to rotate keys for

        Returns:
            Updated CryptoKeysDB record
        """
        try:
            crypto_keys = self.get_user_crypto_keys(db, user_id)
            if not crypto_keys:
                raise ValueError(f"No crypto keys found for user {user_id}")

            # Generate new key pair (keep hash_key and salt)
            new_key_pair = self.key_gen_service.generate_key_pair()

            # Update keys
            crypto_keys.access_key = new_key_pair.access_key
            crypto_keys.secret_key = new_key_pair.secret_key
            crypto_keys.updated_at = datetime.now()

            db.commit()
            db.refresh(crypto_keys)

            logger.info(f"Rotated crypto keys for user {user_id}")
            return crypto_keys

        except Exception as e:
            logger.error(f"Failed to rotate keys for user {user_id}: {str(e)}")
            db.rollback()
            raise
