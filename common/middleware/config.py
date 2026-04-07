"""Middleware configuration utilities."""

from fastapi import FastAPI, HTTPException
from .request_context import RequestContextMiddleware
from .exception_handler import http_exception_handler, general_exception_handler


def setup_middleware(app: FastAPI, service_name: str):
    """
    Setup common middleware for a FastAPI application.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service (e.g., "backend", "process", "ai-provider")
    """
    # 添加请求上下文中间件
    app.add_middleware(RequestContextMiddleware, service_name=service_name)
    
    # 添加异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)