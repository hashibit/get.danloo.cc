"""
Task model enums and classes for Process service - SQLAlchemy 2.0 style
"""

from enum import Enum
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from .base import CommonBase

if TYPE_CHECKING:
    from .job_model import JobDB


class TaskStatus(str, Enum):
    """Task status enumeration with string inheritance for JSON serialization"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskDB(CommonBase):
    """Enhanced Task database model for Process service"""

    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.job_id"), nullable=False, index=True
    )
    material_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    object_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PROCESS_MATERIAL"
    )
    status: Mapped[str] = mapped_column(String(50), default=TaskStatus.PENDING.value)

    # Task execution details
    result: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string of task results
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[str] = mapped_column(String(10), default="0")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to job
    job: Mapped["JobDB"] = relationship("JobDB", back_populates="tasks")
