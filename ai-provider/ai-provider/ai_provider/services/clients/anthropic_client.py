"""Anthropic Claude client implementation using official Anthropic Python library."""

import logging
import time
from functools import wraps
from retrying import retry
from typing import Dict, Any, List, Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from ..utils.token_recorder import ConsoleTokenRecorder
from ...config import global_settings
from ...utils import RateLimiter

logger = logging.getLogger(__name__)


def configurable_retry(func):
    """可配置的重试装饰器"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        retry_decorator = retry(
            stop_max_attempt_number=self.retry_max_attempts,
            wait_exponential_multiplier=self.retry_wait_multiplier,
        )
        return retry_decorator(func)(self, *args, **kwargs)

    return wrapper


class AnthropicClient:
    """Anthropic Claude 客户端 using official Python library"""

    def __init__(self, token_recorder=None):
        if Anthropic is None:
            raise ImportError(
                "Anthropic library is not installed. Please install it with: pip install anthropic"
            )

        self.api_key = global_settings.anthropic.api_key
        self.model = global_settings.anthropic.model
        self.base_url = global_settings.anthropic.base_url

        # Initialize Anthropic client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = Anthropic(**client_kwargs)

        self.rate_limiter = RateLimiter(
            name="Anthropic",
            tokens_per_minute=global_settings.anthropic.tokens_quota_per_minute,
            requests_per_minute=global_settings.anthropic.requests_quota_per_minute,
            window_seconds=60,
        )

        # 重试配置
        self.retry_max_attempts = global_settings.retry_max_attempts
        self.retry_wait_multiplier = global_settings.retry_wait_multiplier

        # 记录 token
        self.token_recorder = token_recorder or ConsoleTokenRecorder()

    @configurable_retry
    def request_anthropic_completion(
        self,
        content_id: int,
        prompt: str,
        text: str,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发送 Anthropic Claude 聊天完成请求

        Args:
            content_id: 内容ID
            prompt: 系统提示词（会放在 system 或 messages 中）
            text: 用户输入文本
            max_tokens: 最大生成 tokens 数
            temperature: 温度参数
            system_message: 可选的系统消息（优先级高于 prompt）

        Returns:
            Dict包含 content(str) 和 metadata(dict)
        """
        logger.info(f"Content ID: {content_id} 调用 Anthropic Claude")

        # 等待速率限制
        self.rate_limiter.wait_for_tokens_and_requests()

        try:
            start_time = time.time()

            # 构建消息
            messages = [
                {"role": "user", "content": text}
            ]

            # 使用 system_message 或 prompt 作为系统消息
            system = system_message if system_message else prompt

            # Create message using official client
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=messages
            )

            duration = time.time() - start_time

            # 提取响应内容
            content_text = ""
            if response.content:
                # Anthropic 返回的是 content blocks
                for block in response.content:
                    if hasattr(block, "text"):
                        content_text += block.text

            # 提取 token 使用信息
            input_tokens = getattr(response.usage, "input_tokens", 0)
            output_tokens = getattr(response.usage, "output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # 记录token使用情况 - 与 OpenAI 客户端保持一致
            self.token_recorder.record_tokens(
                content_id,
                self.model,
                input_tokens,
                output_tokens,
            )

            # 更新速率限制器 - 与 OpenAI 客户端保持一致
            self.rate_limiter.record_request(input_tokens, output_tokens)

            # 打印详细的 response metadata
            logger.info(
                f"Content ID: {content_id} Response metadata - "
                f"id: {response.id}, "
                f"model: {response.model}, "
                f"role: {response.role}, "
                f"stop_reason: {response.stop_reason}, "
                f"stop_sequence: {response.stop_sequence}, "
                f"type: {response.type}"
            )

            metadata = {
                "model": self.model,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens,
                "duration_seconds": duration,
                "finish_reason": response.stop_reason or "stop",
                "stop_sequence": response.stop_sequence,
                "response_id": response.id,
                "response_type": response.type,
                "response_role": response.role,
            }

            logger.info(
                f"Content ID: {content_id} Anthropic完成 "
                f"(tokens: {total_tokens}, duration: {duration:.2f}s)"
            )

            return {
                "content": content_text,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Content ID: {content_id} Anthropic API调用失败: {str(e)}")
            raise

    def request_anthropic_chat_completion(
        self, content_id: int, prompt: str, text: str
    ) -> Dict[str, Any]:
        """
        兼容接口：发送 Anthropic 聊天完成请求
        保持与 OpenAICompletion 相同的接口
        """
        return self.request_anthropic_completion(
            content_id=content_id,
            prompt=prompt,
            text=text
        )
