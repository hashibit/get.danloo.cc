"""
Job model enums and classes for Process service - SQLAlchemy 2.0 style
"""

from enum import Enum
from sqlalchemy import String, DateTime, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Any, List, TYPE_CHECKING
from .base import CommonBase

if TYPE_CHECKING:
    from .task_model import TaskDB


class JobType(str, Enum):
    """Job type enumeration with string inheritance for JSON serialization"""

    MATERIAL_PROCESSING = "material_processing"
    PELLET_GENERATION = "pellet_generation"
    BATCH_ANALYSIS = "batch_analysis"


class JobStatus(str, Enum):
    """Job status enumeration with string inheritance for JSON serialization"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobDB(CommonBase):
    """Enhanced Job database model for Process service"""

    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=JobType.MATERIAL_PROCESSING.value
    )
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.PENDING.value)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    job_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )  # Store job-specific metadata
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to tasks
    tasks: Mapped[List["TaskDB"]] = relationship(
        "TaskDB", back_populates="job", cascade="all, delete-orphan"
    )
