"""
Process Service API models for inter-service communication
"""

from pydantic import BaseModel
from typing import Any, Optional


# Material info for pellet generation
class MaterialInfo(BaseModel):
    """Material information for pellet generation"""

    id: str
    content_type: str
    file_path: str
    file_size: int


# New models for intelligent pellet generation
class PelletGenerationRequest(BaseModel):
    """Request for intelligent pellet generation from materials"""

    materials: list[MaterialInfo]
    user_id: str


class PelletGenerationResponse(BaseModel):
    """Response from pellet generation request"""

    job_id: str
    status: str
    message: str
    estimated_pellets: Optional[int] = None
