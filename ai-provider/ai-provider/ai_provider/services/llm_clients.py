"""LLM client implementations for different providers."""

import logging

logger = logging.getLogger(__name__)


# 全局实例 - 使用懒加载避免初始化问题
_openai_completion = None
_bedrock_cluster = None
_ark_client = None
_anthropic_client = None


def get_openai_completion():
    global _openai_completion
    if _openai_completion is None:
        from .clients.openai_client import OpenAICompletion

        _openai_completion = OpenAICompletion()
    return _openai_completion


def get_bedrock_cluster():
    global _bedrock_cluster
    if _bedrock_cluster is None:
        from .clients.bedrock_cluster import BedrockCluster

        _bedrock_cluster = BedrockCluster()
    return _bedrock_cluster


def get_ark_client():
    global _ark_client
    if _ark_client is None:
        try:
            from .clients.ark_client import ArkClient

            _ark_client = ArkClient()
        except Exception as e:
            logger.warning(f"ArkClient初始化失败，返回None: {e}")
            _ark_client = None
    return _ark_client


def get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        try:
            from .clients.anthropic_client import AnthropicClient

            _anthropic_client = AnthropicClient()
        except Exception as e:
            logger.warning(f"AnthropicClient初始化失败，返回None: {e}")
            _anthropic_client = None
    return _anthropic_client
