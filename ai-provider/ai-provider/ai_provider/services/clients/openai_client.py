"""OpenAI client implementation using official OpenAI Python library."""

import logging
import time
from functools import wraps
from retrying import retry

try:
    import openai
except ImportError:
    openai = None

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


class OpenAICompletion:
    """OpenAI客户端 using official Python library"""

    def __init__(self, token_recorder=None):
        if openai is None:
            raise ImportError(
                "OpenAI library is not installed. Please install it with: pip install openai"
            )

        self.token = global_settings.openai.token
        self.model = global_settings.openai.model
        self.base_url = global_settings.openai.url

        # Initialize OpenAI client
        self.client = openai.OpenAI(
            api_key=self.token,
            base_url=self.base_url if self.base_url else None,
        )

        self.rate_limiter = RateLimiter(
            name="OpenAI",
            tokens_per_minute=global_settings.openai.tokens_quota_per_minute,
            requests_per_minute=global_settings.openai.requests_quota_per_minute,
            window_seconds=60,
        )

        # 重试配置
        self.retry_max_attempts = global_settings.retry_max_attempts
        self.retry_wait_multiplier = global_settings.retry_wait_multiplier

        # 记录 token
        self.token_recorder = token_recorder or ConsoleTokenRecorder()

    @configurable_retry
    def request_openai_chat_completion(
        self, content_id: int, prompt: str, text: str
    ) -> str:
        """发送OpenAI聊天完成请求 using official client"""
        logger.info(f"Content ID: {content_id} 调用OpenAI")

        # 等待速率限制
        self.rate_limiter.wait_for_tokens_and_requests()

        try:
            # Create chat completion using official client
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                max_tokens=8192,
                temperature=0.7,
            )

            logger.info(
                f"OpenAI completion response received, resposne: {response.model_dump()}"
            )

            content = response.choices[0].message.content

            # 记录token使用
            usage = response.usage
            if usage:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens

                self.rate_limiter.record_request(prompt_tokens, completion_tokens)

                self.token_recorder.record_tokens(
                    content_id,
                    self.model,
                    prompt_tokens,
                    completion_tokens,
                )

                logger.info(
                    f"Content ID: {content_id}, 模型 {self.model} 输入 Token: {prompt_tokens} 输出 Token: {completion_tokens}"
                )

            return content

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {e}")
            # Wait longer if rate limited
            time.sleep(5)
            raise
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise
        except openai.TimeoutError as e:
            logger.error(f"OpenAI timeout error: {e}")
            raise
        except Exception as e:
            logger.error(f"OpenAI调用失败: {e}")
            raise

    def get_model_info(self):
        """获取模型信息"""
        try:
            models = self.client.models.list()
            return {"available_models": [model.id for model in models.data]}
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}
