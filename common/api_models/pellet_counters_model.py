from pydantic import BaseModel, ConfigDict
from datetime import datetime
from common.database_models.pellet_counters_model import PelletCountersDB


class PelletCountersBase(BaseModel):
    """Base model for pellet counters"""

    pass


class PelletCountersCreate(PelletCountersBase):
    """Model for creating pellet counters"""

    pellet_id: str


class PelletCountersResponse(PelletCountersBase):
    """Model for pellet counters response"""

    pellet_id: str
    view_count: int = 0
    like_count: int = 0
    estimated_read_time: int = 0  # in minutes
    referenced_material_count: int = 0
    referenced_job_count: int = 0
    referenced_pellet_count: int = 0
    referenced_by_pellet_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
