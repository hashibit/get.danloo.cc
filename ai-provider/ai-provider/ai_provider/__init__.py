"""LLM Proxy Module

A modular service for handling LLM interactions with multiple backends.
"""

__version__ = "1.0.0"
__author__ = "AI Team"

from .config import global_settings
from .models import *
from .services.llm_caller import llm_caller

__all__ = [
    "global_settings",
    "llm_caller",
    # Models
    "ClassificationResult",
    "Category",
    "Tag",
    # Request models
    "ExtractContentRequest",
]
