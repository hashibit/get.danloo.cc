"""Custom exception handler that preserves token usage information."""

import logging
import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.responses import Response
from ..utils.request_context import get_current_context
import time

logger = logging.getLogger(__name__)


def add_context_headers_to_response(response: Response, log_success: bool = True):
    """Add context information to any response"""
    try:
        final_context = get_current_context()
        request_duration = time.time() - final_context.start_time

        # 添加基本响应头
        response.headers["X-Request-UUID"] = final_context.request_uuid
        response.headers["X-Request-Duration"] = f"{request_duration:.3f}s"

        # 添加请求路径和服务名
        response.headers["X-Request-Path"] = final_context.request_path
        if final_context.service_name:
            response.headers["X-Service-Name"] = final_context.service_name

        # 只有在有token使用时才添加token相关头
        if final_context.token_usage.model_usages:
            # 新格式: {model_id:model1,input_tokens:100,output_tokens:50,request_path:/api/classify}{model_id:model2,...}
            response.headers["X-Token-Usage"] = (
                final_context.token_usage.to_header_string(final_context.request_path)
            )

        # 记录成功日志（只在成功请求时记录）
        if log_success and response.status_code < 400:
            models_used = final_context.token_usage.get_models()
            usage_count = len(final_context.token_usage.model_usages)
            service_prefix = (
                f"[{final_context.service_name}] " if final_context.service_name else ""
            )

            logger.info(
                f"{service_prefix}Request completed - "
                f"Content ID: {final_context.content_id if final_context.content_id > 0 else 'N/A'}, "
                f"Path: {final_context.request_path}, "
                f"Duration: {request_duration:.3f}s, "
                f"LLM Calls: {usage_count}, "
                f"Models: {', '.join(models_used) if models_used else 'None'}"
            )

    except Exception as e:
        # 如果添加头部失败，不要影响原响应
        logger.warning(f"Failed to add context headers: {e}")


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom HTTPException handler that preserves token usage info"""
    final_context = get_current_context()
    request_duration = time.time() - final_context.start_time

    models_used = final_context.token_usage.get_models()
    usage_count = len(final_context.token_usage.model_usages)
    service_prefix = (
        f"[{final_context.service_name}] " if final_context.service_name else ""
    )

    logger.error(
        f"{service_prefix}HTTPException - "
        f"Content ID: {final_context.content_id if final_context.content_id > 0 else 'N/A'}, "
        f"Path: {final_context.request_path}, "
        f"Status: {exc.status_code}, Duration: {request_duration:.3f}s, "
        f"Error: [{exc.detail}], "
        f"LLM Calls: {usage_count}, "
        f"Models: {', '.join(models_used) if models_used else 'None'}"
    )

    # # 对于 500 错误，也记录堆栈信息（如果有的话）
    # if exc.status_code >= 500:
    #     logger.error(
    #         f"{service_prefix}HTTPException stack trace:\n{traceback.format_exc()}"
    #     )

    # 创建标准的 HTTPException 响应
    response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # 添加上下文信息到响应头（不记录成功日志，因为这是异常）
    add_context_headers_to_response(response, log_success=False)

    return response


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """General exception handler for unexpected errors"""
    final_context = get_current_context()
    request_duration = time.time() - final_context.start_time

    models_used = final_context.token_usage.get_models()
    usage_count = len(final_context.token_usage.model_usages)
    service_prefix = (
        f"[{final_context.service_name}] " if final_context.service_name else ""
    )

    # 记录异常基本信息
    logger.error(
        f"{service_prefix}Unexpected error - "
        f"Content ID: {final_context.content_id if final_context.content_id > 0 else 'N/A'}, "
        f"Path: {final_context.request_path}, "
        f"Duration: {request_duration:.3f}s, "
        f"Error: [{str(exc)}], "
        f"LLM Calls before error: {usage_count}, "
        f"Models: {', '.join(models_used) if models_used else 'None'}"
    )

    # # 记录完整的异常堆栈
    # logger.error(
    #     f"{service_prefix}Exception stack trace:\n{traceback.format_exc()}"
    # )

    # 创建 500 错误响应
    response = JSONResponse(status_code=500, content={"detail": str(exc)})

    # 添加上下文信息到响应头（不记录成功日志，因为这是异常）
    add_context_headers_to_response(response, log_success=False)

    return response
