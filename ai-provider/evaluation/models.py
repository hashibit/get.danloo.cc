"""
模型函数定义模块

定义各种用于精度测试的模型函数
"""

import sys
import os
import logging
import inspect
from typing import Dict, Any, Optional, Callable

# 添加llm-proxy到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "llm-proxy"))

logger = logging.getLogger(__name__)


def get_method_params(method):
    """获取方法的参数列表"""
    sig = inspect.signature(method)
    return list(sig.parameters.keys())


def bedrock_classify_video_is_funny() -> Callable:
    """
    返回一个只校验必要参数的模型函数，其余参数自动透传
    """
    from llm_proxy.services.llm_caller import LLMCaller

    llm_caller = LLMCaller()

    # 被测试的模型
    model_func = llm_caller.analyze_video_is_funny_with_bedrock
    model_func_params = get_method_params(model_func)

    logger.info(f"bedrock方法参数: {model_func_params}")

    def inner(**kwargs) -> int:
        """
        分析视频是否有趣的模型函数
        必须参数: content_id, video_url
        其余参数自动透传
        """
        content_id = kwargs.get("content_id")
        video_url = kwargs.get("video_url")
        if not content_id or not video_url:
            logger.error(
                f"缺少必要参数: content_id={content_id}, video_url={video_url}"
            )
            return 0
        try:
            # 动态过滤参数，只保留方法真正需要的
            valid_params = {
                k: v
                for k, v in kwargs.items()
                if k in model_func_params and k not in ["content_id", "video_url"]
            }
            result = model_func(
                content_id=int(content_id), http_video_url=video_url, **valid_params
            )
            return 1 if result.is_funny else 0
        except Exception as e:
            logger.error(f"模型执行失败: {e}")
            return 0

    return inner


def ark_classify_video_is_funny() -> Callable:
    """
    返回一个只校验必要参数的模型函数，其余参数自动透传
    """
    from llm_proxy.services.llm_caller import LLMCaller

    llm_caller = LLMCaller()

    # 被测试的模型
    model_func = llm_caller.analyze_video_is_funny_with_ark
    model_func_params = get_method_params(model_func)
    logger.info(f"ark方法参数: {model_func_params}")

    def inner(**kwargs) -> int:
        """
        分析视频是否有趣的模型函数
        必须参数: content_id, video_url
        其余参数自动透传
        """
        content_id = kwargs.get("content_id")
        video_url = kwargs.get("video_url")
        if not content_id or not video_url:
            logger.error(
                f"缺少必要参数: content_id={content_id}, video_url={video_url}"
            )
            return 0
        try:
            # 动态过滤参数，只保留方法真正需要的
            valid_params = {
                k: v
                for k, v in kwargs.items()
                if k in model_func_params and k not in ["content_id", "video_url"]
            }
            result = model_func(
                content_id=int(content_id), http_video_url=video_url, **valid_params
            )
            return 1 if result.is_funny else 0
        except Exception as e:
            logger.error(f"模型执行失败: {e}")
            return 0

    return inner


# 模型注册表工厂
MODEL_FACTORY_REGISTRY = {
    "bedrock.classify_video_is_funny": bedrock_classify_video_is_funny,
    "ark.classify_video_is_funny": ark_classify_video_is_funny,
}


def get_model_function(model_name: str):
    """
    根据模型名称获取模型函数
    """
    if model_name not in MODEL_FACTORY_REGISTRY:
        available_models = list(MODEL_FACTORY_REGISTRY.keys())
        raise ValueError(f"模型 '{model_name}' 不存在。可用模型: {available_models}")
    return MODEL_FACTORY_REGISTRY[model_name]()


def list_available_models() -> list:
    """
    列出所有可用的模型
    """
    return list(MODEL_FACTORY_REGISTRY.keys())
