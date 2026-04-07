"""
Common Pellet database model
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import CommonBase
from .tag_model import pellet_tags


class PelletDB(CommonBase):
    """Pellet database model - shared across services"""

    __tablename__ = "pellets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    material_ids: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="in-queue")

    ai_score: Mapped[Optional[float]] = mapped_column(Float)
    pellet_type: Mapped[Optional[str]] = mapped_column(String(50))
    generation_metadata: Mapped[Optional[str]] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(10), default="private")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    tags: Mapped[List["TagDB"]] = relationship(
        "TagDB", secondary=pellet_tags, back_populates="pellets"
    )
    counters: Mapped[Optional["PelletCountersDB"]] = relationship(
        "PelletCountersDB", uselist=False, back_populates="pellet"
    )
