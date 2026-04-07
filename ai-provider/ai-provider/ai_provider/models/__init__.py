from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum


class LLMRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_used: int
    success: bool
    error: Optional[str] = None
