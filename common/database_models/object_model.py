"""
Common Object database model
"""

from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from .base import CommonBase


class ObjectDB(CommonBase):
    """Object database model - shared across backend and process services"""

    __tablename__ = "objects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    s3_path: Mapped[str] = mapped_column(String(512))
    presigned_url: Mapped[Optional[str]] = mapped_column(Text)
    file_info: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    is_uploaded: Mapped[bool] = mapped_column(Boolean, server_default=func.text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
