"""
Common Pellet Counters database model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import CommonBase


class PelletCountersDB(CommonBase):
    """Pellet counters database model - shared across services"""

    __tablename__ = "pellet_counters"

    pellet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pellets.id", ondelete="CASCADE"), primary_key=True
    )
    view_count: Mapped[int] = mapped_column(
        Integer, server_default=func.text("0")
    )
    like_count: Mapped[int] = mapped_column(
        Integer, server_default=func.text("0")
    )
    estimated_read_time: Mapped[int] = mapped_column(
        Integer, server_default=func.text("0")
    )
    referenced_material_count: Mapped[int] = mapped_column(
        Integer, server_default=func.text("0")
    )
    referenced_job_count: Mapped[int] = mapped_column(
        Integer, server_default=func.text("0")
    )
    referenced_pellet_count: Mapped[int] = mapped_column(
        Integer, server_default=func.text("0")
    )
    referenced_by_pellet_count: Mapped[int] = mapped_column(
        Integer, server_default=func.text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    pellet: Mapped["PelletDB"] = relationship("PelletDB", back_populates="counters")
