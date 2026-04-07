from pydantic import BaseModel, ConfigDict
from datetime import datetime
from common.database_models.tag_model import TagDB


class TagData(BaseModel):
    id: str
    name: str
    color: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
