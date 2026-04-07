"""
Common User database model - SQLAlchemy 2.0 style
"""

from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from common.utils.ulid_utils import generate_ulid
from .base import CommonBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .crypto_keys_model import CryptoKeysDB
    from .social_account_model import SocialAccountDB


class UserDB(CommonBase):
    """User database model - shared across services"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, index=True, default=generate_ulid
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    username: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, index=True, nullable=True
    )
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    wechat_openid: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    wechat_unionid: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    wechat_nickname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    wechat_avatar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exp_level: Mapped[str] = mapped_column(String(10), default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to crypto keys
    crypto_keys: Mapped[Optional["CryptoKeysDB"]] = relationship(
        "CryptoKeysDB", back_populates="user", uselist=False
    )

    # Relationship to social accounts
    social_accounts: Mapped[list["SocialAccountDB"]] = relationship(
        "SocialAccountDB", back_populates="user", cascade="all, delete-orphan"
    )
