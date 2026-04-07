"""Configuration settings for AI Proxy."""

import os
from dataclasses import dataclass


@dataclass
class OpenAIConfig:
    """OpenAI configuration."""

    url: str
    token: str
    model: str
    requests_quota_per_minute: int
    tokens_quota_per_minute: int


@dataclass
class AnthropicConfig:
    """Anthropic Claude configuration."""

    api_key: str
    base_url: str
    model: str
    requests_quota_per_minute: int
    tokens_quota_per_minute: int


class Settings:
    """Main settings class for AI Proxy."""

    def __init__(self):
        # OpenAI配置
        self.openai = OpenAIConfig(
            url=os.getenv("OPENAI_URL", "https://api.openai.com/v1"),
            token=os.getenv("OPENAI_TOKEN", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            requests_quota_per_minute=int(
                os.getenv("OPENAI_REQUESTS_QUOTA_PER_MINUTE", "1000")
            ),
            tokens_quota_per_minute=int(
                os.getenv("OPENAI_TOKENS_QUOTA_PER_MINUTE", "1000000")
            ),
        )

        # Anthropic配置
        self.anthropic = AnthropicConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            base_url=os.getenv("ANTHROPIC_BASE_URL", ""),
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            requests_quota_per_minute=int(
                os.getenv("ANTHROPIC_REQUESTS_QUOTA_PER_MINUTE", "1000")
            ),
            tokens_quota_per_minute=int(
                os.getenv("ANTHROPIC_TOKENS_QUOTA_PER_MINUTE", "1000000")
            ),
        )

        # 重试配置
        self.retry_max_attempts = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
        self.retry_wait_multiplier = int(os.getenv("RETRY_WAIT_MULTIPLIER", "1000"))


# 全局配置实例
global_settings = Settings()