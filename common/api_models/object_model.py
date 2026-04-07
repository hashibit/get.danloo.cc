from typing import Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FileInfo(BaseModel):
    """Model for file information"""
    size: int | None = None
    type: str | None = None
    uploaded_by: str | None = None
    filename: str | None = None
    source_url: str | None = None
    content_type: str | None = None
    input_type: str | None = None
    additional_metadata: dict[str, Any] | None = None

class ObjectBase(BaseModel):
    """Base model for objects"""

    name: str

class ObjectCreate(ObjectBase):
    """Model for creating objects"""

    file_info: FileInfo | None = None

class ObjectUpdate(BaseModel):
    """Model for updating objects"""

    name: str | None = None
    file_info: FileInfo | None = None
    is_uploaded: bool | None = None

class ObjectResponse(ObjectBase):
    """Model for object responses"""

    id: str
    s3_path: str
    presigned_url: str | None = None
    file_info: FileInfo | None = None
    is_uploaded: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
