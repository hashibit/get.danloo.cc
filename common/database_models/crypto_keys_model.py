"""
Common Crypto Keys database model - SQLAlchemy 2.0 style
"""

from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .base import CommonBase


class CryptoKeysDB(CommonBase):
    """Crypto keys database model - shared across services"""

    __tablename__ = "crypto_keys"

    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.id"), primary_key=True, index=True
    )
    access_key: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    secret_key: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Encrypted in storage
    hash_key: Mapped[str] = mapped_column(Text, nullable=False)
    salt: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to user
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="crypto_keys")
