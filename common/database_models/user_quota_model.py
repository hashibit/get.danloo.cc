"""
User quota database models - SQLAlchemy 2.0 style
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, DateTime, Date, Boolean, Text, Index, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from .base import CommonBase
from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from .user_model import UserDB  # unused


class UserQuotaDB(CommonBase):
    """User quota database model - tracks daily quota limits and usage"""

    __tablename__ = "user_quotas"

    id: Mapped[int] = mapped_column(
        primary_key=True, 
        autoincrement=True, 
        comment="Primary key ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(255), 
        ForeignKey('users.id'), 
        nullable=False, 
        index=True,
        comment="User ID reference"
    )
    quota_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default='credits',
        comment="Quota type (credits, tokens, etc.)"
    )
    daily_limit: Mapped[float] = mapped_column(
        Numeric(15, 6), 
        nullable=False, 
        default=0.0,
        comment="Daily quota limit"
    )
    used_amount: Mapped[float] = mapped_column(
        Numeric(15, 6), 
        nullable=False, 
        default=0.0,
        comment="Amount used today"
    )
    reset_date: Mapped[date] = mapped_column(
        Date, 
        nullable=False,
        comment="Quota reset date"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Whether the quota is active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        comment="Last update timestamp"
    )

    # Table-level configuration and indexes
    __table_args__ = (
        Index(
            'idx_user_quota_date', 
            'user_id', 
            'quota_type', 
            'reset_date', 
            unique=True
        ),
        Index('idx_reset_date', 'reset_date'),
        Index('idx_user_active', 'user_id', 'is_active'),
        Index('idx_quota_type', 'quota_type'),
        {
            'comment': 'User daily quota tracking table',
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci'
        }
    )

    def __repr__(self) -> str:
        return (
            f"<UserQuotaDB(id={self.id}, user_id={self.user_id}, "
            f"quota_type={self.quota_type}, daily_limit={self.daily_limit}, "
            f"used_amount={self.used_amount}, reset_date={self.reset_date})>"
        )

    @property
    def remaining_amount(self) -> float:
        """Calculate remaining quota amount"""
        return max(0.0, float(self.daily_limit) - float(self.used_amount))

    @property
    def usage_percentage(self) -> float:
        """Calculate quota usage percentage"""
        if self.daily_limit == 0:
            return 0.0
        return min(100.0, (float(self.used_amount) / float(self.daily_limit)) * 100)

    def is_quota_sufficient(self, amount: float) -> bool:
        """Check if quota is sufficient for the requested amount"""
        return self.is_active and self.remaining_amount >= amount

    def is_reset_needed(self, current_date: date) -> bool:
        """Check if quota needs to be reset for the current date"""
        return self.reset_date < current_date


class QuotaUsageLogDB(CommonBase):
    """Quota usage log database model - tracks all quota operations"""

    __tablename__ = "quota_usage_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True, 
        autoincrement=True,
        comment="Primary key ID"
    )
    user_id: Mapped[str] = mapped_column(
        String(255), 
        ForeignKey('users.id'), 
        nullable=False, 
        index=True,
        comment="User ID reference"
    )
    quota_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Quota type (credits, tokens, etc.)"
    )
    amount: Mapped[float] = mapped_column(
        Numeric(15, 6), 
        nullable=False,
        comment="Operation amount (positive for consumption, negative for refund)"
    )
    operation_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="Operation type: consume, refund, reset, upgrade"
    )
    related_request_uuid: Mapped[Optional[str]] = mapped_column(
        String(36), 
        nullable=True,
        comment="Related request UUID (if applicable)"
    )
    quota_before: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 6), 
        nullable=True,
        comment="Quota amount before operation"
    )
    quota_after: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 6), 
        nullable=True,
        comment="Quota amount after operation"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        comment="Operation description"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Operation timestamp"
    )

    # Table-level configuration and indexes
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'created_at'),
        Index('idx_request_uuid', 'related_request_uuid'),
        Index('idx_operation_type', 'operation_type'),
        Index('idx_quota_type', 'quota_type'),
        Index('idx_created_at', 'created_at'),
        {
            'comment': 'Quota usage operation log table',
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci'
        }
    )

    def __repr__(self) -> str:
        return (
            f"<QuotaUsageLogDB(id={self.id}, user_id={self.user_id}, "
            f"operation_type={self.operation_type}, amount={self.amount}, "
            f"created_at={self.created_at})>"
        )