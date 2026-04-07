"""
Common Tag database model
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, Text, Table, ForeignKey, Column
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import CommonBase

# Association table for many-to-many relationship between pellets and tags
pellet_tags = Table(
    "pellet_tags",
    CommonBase.metadata,
    Column("pellet_id", String(255), ForeignKey("pellets.id"), primary_key=True),
    Column("tag_id", String(255), ForeignKey("tags.id"), primary_key=True),
)


class TagDB(CommonBase):
    """Tag database model - shared across services"""

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    pellets: Mapped[List["PelletDB"]] = relationship(
        "PelletDB", secondary=pellet_tags, back_populates="tags"
    )
