"""Common decorators for API endpoints."""

import functools
import contextvars
import asyncio
from typing import Callable, Any, TypeVar
from collections.abc import Coroutine

from fastapi import HTTPException

from ai_provider.utils.logging_config import setup_logging
from ai_provider.services.utils.video_processor import FFmpegException
from ai_provider.models.requests import InvalidRequestException
from common.utils.request_context import set_content_id
from ai_provider import global_settings

from common.api_models.ai_provider import BaseRequest

logger = setup_logging(global_settings.logging)

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


def _find_request_obj(*args, **kwargs) -> BaseRequest | None:
    # 查找BaseRequest对象（请求体对象）
    # 检查位置参数
    for arg in args:
        if isinstance(arg, BaseRequest):
            return arg

    # 检查关键字参数
    for value in kwargs.values():
        if isinstance(value, BaseRequest):
            return value

    return None


def auto_set_content_id(func: F) -> F:
    """自动设置content_id到请求上下文"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if request := _find_request_obj(*args, **kwargs):
            set_content_id(request.content_id)
        return await func(*args, **kwargs)

    return wrapper


def handle_api_exceptions(func: F) -> F:
    """统一的异常处理装饰器"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        operation_name = func.__name__
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except InvalidRequestException as e:
            raise HTTPException(status_code=400, detail=e.message)
        except FFmpegException as e:
            request = args[0] if args else None
            video_url = getattr(request, "http_video_url", "unknown")
            logger.error(
                f"Bad video? {video_url}, FFmpegException in {operation_name}",
                exc_info=e,
            )
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error in {operation_name}", exc_info=e)
            raise HTTPException(status_code=500, detail=str(e))

    return wrapper


async def run_in_executor_with_context(executor, func, *args):
    """Run function in executor while preserving context"""
    ctx = contextvars.copy_context()
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, ctx.run, func, *args)


async def execute_llm_operation(executor, operation_func, content_id: int, *args):
    """统一的LLM操作执行函数"""
    operation_name = operation_func.__name__.replace("_", " ")
    logger.info(f"Received {operation_name} request for content_id: {content_id}")
    return await run_in_executor_with_context(
        executor, operation_func, content_id, *args
    )
