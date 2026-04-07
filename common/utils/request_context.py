"""Request context for storing data across the request lifecycle."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Dict, List
import json


@dataclass
class ModelTokenUsage:
    """Token usage for a specific model - single record"""

    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "model_id": self.model_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass
class TokenUsage:
    """Multi-model token usage tracking - each usage is a separate record"""

    model_usages: List[ModelTokenUsage] = field(default_factory=list)

    def add_usage(self, input_tokens: int, output_tokens: int, model_id: str):
        """Add token usage as a separate record"""
        usage = ModelTokenUsage(
            model_id=model_id, input_tokens=input_tokens, output_tokens=output_tokens
        )
        self.model_usages.append(usage)

    def get_models(self) -> List[str]:
        """Get list of unique model IDs used"""
        return list(set(usage.model_id for usage in self.model_usages))

    def to_header_string(self, request_path: str = "") -> str:
        """Convert to response header format: {model_id:model1,input_tokens:100,output_tokens:50,request_path:/api/classify}{model_id:model2,...}"""
        if not self.model_usages:
            return ""

        model_parts = []
        for usage in self.model_usages:
            model_parts.append(
                f"model_id:{usage.model_id},input_tokens:{usage.input_tokens},output_tokens:{usage.output_tokens},request_path:{request_path}"
            )

        return "{" + "}{".join(model_parts) + "}"


@dataclass
class RequestContext:
    """Request context data"""

    content_id: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    user_agent: str = ""
    request_uuid: str = ""
    start_time: float = 0.0
    request_path: str = ""
    service_name: str = ""  # 添加服务名称标识


# Context variable for storing request data
request_context: ContextVar[RequestContext] = ContextVar(
    "request_context", default=RequestContext()
)


def get_current_context() -> RequestContext:
    """Get current request context"""
    return request_context.get()


def set_current_context(context: RequestContext):
    """Set current request context"""
    request_context.set(context)


def add_token_usage(input_tokens: int, output_tokens: int, model_id: str):
    """Add token usage to current request context"""
    if not model_id:
        raise ValueError("model_id is required for token usage tracking")

    context = get_current_context()
    context.token_usage.add_usage(input_tokens, output_tokens, model_id)


def get_token_usage() -> TokenUsage:
    """Get token usage from current request context"""
    context = get_current_context()
    return context.token_usage


def set_content_id(content_id: int):
    """Set content ID in current request context"""
    context = get_current_context()
    context.content_id = content_id


def set_service_name(service_name: str):
    """Set service name in current request context"""
    context = get_current_context()
    context.service_name = service_name