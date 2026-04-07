"""Request context middleware for FastAPI."""

import time
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..utils.request_context import (
    RequestContext,
    set_current_context,
    get_current_context,
    set_service_name,
)
from ..utils.ulid_utils import generate_ulid
from .exception_handler import add_context_headers_to_response
import logging

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to manage request context throughout the request lifecycle"""
    
    def __init__(self, app, service_name: str = ""):
        """
        Initialize middleware with service name
        
        Args:
            app: FastAPI application instance
            service_name: Name of the service (e.g., "backend", "process", "ai-provider")
        """
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        # 创建新的请求上下文
        context = RequestContext(
            request_uuid=generate_ulid(),
            user_agent=request.headers.get("user-agent", ""),
            start_time=time.time(),
            request_path=request.url.path,  # 只获取路径部分，不包含query
            service_name=self.service_name,
        )

        # 设置上下文
        set_current_context(context)

        try:
            # 处理请求
            response = await call_next(request)

            # 添加token使用信息到响应头
            add_context_headers_to_response(response)

            return response

        except Exception:
            # 让异常继续传播，由异常处理器处理
            raise