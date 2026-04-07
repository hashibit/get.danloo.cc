"""
Verification Code database model - SQLAlchemy 2.0 style
"""

from sqlalchemy import String, DateTime, Integer, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import CommonBase


class VerificationCode(CommonBase):
    """Verification code database model for phone/SMS verification"""

    __tablename__ = "verification_codes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    phone_number: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(
        String(10), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False  # 'login', 'register', 'phone_verification'
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    attempts: Mapped[int] = mapped_column(
        Integer, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )