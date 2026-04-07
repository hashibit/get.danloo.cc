"""
Blacklist database model - SQLAlchemy 2.0 style
"""

from sqlalchemy import String, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from common.utils.ulid_utils import generate_ulid
from .base import CommonBase
import enum


class BlacklistType(str, enum.Enum):
    """Blacklist entry type enum"""
    IP = "ip"
    USER = "user"


class BlacklistDB(CommonBase):
    """Blacklist database model for IP and user blocking"""

    __tablename__ = "blacklist"

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, index=True, default=generate_ulid
    )
    identifier: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
        comment="IP address or user ID"
    )
    type: Mapped[BlacklistType] = mapped_column(
        Enum(BlacklistType), nullable=False, index=True,
        comment="Type of blacklist entry: ip or user"
    )
    reason: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Reason for blacklisting"
    )
    created_by: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Admin or system that created this entry"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True,
        comment="Whether this blacklist entry is active"
    )
    extra_data: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON metadata for additional information"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="When this entry was created"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
        comment="When this entry expires (NULL for permanent)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update time"
    )

    def __repr__(self):
        return f"<BlacklistDB(id={self.id}, type={self.type}, identifier={self.identifier}, active={self.is_active})>"
