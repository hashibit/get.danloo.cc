"""
统一的日志配置模块，供所有微服务使用
"""

from .setup import setup_logging, setup_basic_logging
from .utils import get_logger

__all__ = ["setup_logging", "setup_basic_logging", "get_logger"]