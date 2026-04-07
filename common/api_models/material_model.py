from pydantic import BaseModel, ConfigDict
from datetime import datetime
from common.database_models.material_model import MaterialDB


class MaterialCreate(BaseModel):
    title: str
    content_type: str
    file_size: int | None

    model_config = ConfigDict(from_attributes=True)


class MaterialData(BaseModel):
    title: str
    content_type: str
    id: str
    user_id: str
    file_path: str
    file_size: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialListResponse(BaseModel):
    materials: list[MaterialData]
    pagination: dict


class MaterialFromObjectCreate(BaseModel):
    title: str
    content_type: str
    file_object_id: str


class MaterialFromUrlCreate(BaseModel):
    title: str
    url: str
    content_type: str


class MaterialFromTextCreate(BaseModel):
    title: str
    text_content: str
    content_type: str


class MaterialContentData(BaseModel):
    """Material content data with base64 encoded content for AI processing"""
    material_id: str
    object_id: str
    title: str
    content_type: str
    content_base64: str  # Base64 encoded content for AI provider
    file_size: str | None
    user_id: str

    model_config = ConfigDict(from_attributes=True)
