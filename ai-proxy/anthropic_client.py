"""Anthropic Claude client for AI Proxy service."""

import os
import logging
from typing import Dict, Any, Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

logger = logging.getLogger(__name__)


class AnthropicCompletion:
    """Anthropic Claude 客户端"""

    def __init__(self):
        if Anthropic is None:
            raise ImportError(
                "Anthropic library is not installed. Please install it with: pip install anthropic"
            )

        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        # Initialize Anthropic client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = Anthropic(**client_kwargs)

        logger.info(f"Anthropic client initialized with model: {self.model}")
        if self.base_url:
            logger.info(f"Using custom base_url: {self.base_url}")

    def request_anthropic_chat_completion(
        self,
        content_id: int,
        prompt: str,
        text: str,
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ) -> Dict[str, Any]:
        """
        发送 Anthropic Claude 聊天完成请求

        Args:
            content_id: 内容ID
            prompt: 系统提示词
            text: 用户输入文本
            max_tokens: 最大生成 tokens 数
            temperature: 温度参数

        Returns:
            Dict包含 content(str) 和 metadata(dict)
        """
        logger.info(f"Content ID: {content_id} 调用 Anthropic Claude")

        try:
            # 构建消息
            messages = [
                {"role": "user", "content": text}
            ]

            # Create message using official client
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=prompt,
                messages=messages
            )

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
                "finish_reason": response.stop_reason or "stop",
                "stop_sequence": response.stop_sequence,
                "response_id": response.id,
                "response_type": response.type,
                "response_role": response.role,
            }

            logger.info(
                f"Content ID: {content_id} Anthropic完成 "
                f"(tokens: {total_tokens})"
            )

            return {
                "content": content_text,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Content ID: {content_id} Anthropic API调用失败: {str(e)}")
            raise
