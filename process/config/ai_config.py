"""
AI Provider Service configuration
"""

import os
from typing import Optional


class AIConfig:
    """AI Provider服务配置"""

    # AI Provider服务URL
    AI_PROVIDER_URL: str = os.environ.get("AI_PROVIDER_URL", "http://localhost:8002")

    # AI Provider服务超时时间（秒）
    AI_PROVIDER_TIMEOUT: int = int(os.environ.get("AI_PROVIDER_TIMEOUT", "180"))

    # AI Provider服务重试次数
    AI_PROVIDER_RETRY_COUNT: int = int(os.environ.get("AI_PROVIDER_RETRY_COUNT", "3"))

    # AI Provider服务重试延迟（秒）
    AI_PROVIDER_RETRY_DELAY: float = float(
        os.environ.get("AI_PROVIDER_RETRY_DELAY", "1.0")
    )

    # 是否启用AI处理
    ENABLE_AI_PROCESSING: bool = (
        os.environ.get("ENABLE_AI_PROCESSING", "true").lower() == "true"
    )

    # AI处理失败时的回退策略
    AI_FALLBACK_STRATEGY: str = os.environ.get(
        "AI_FALLBACK_STRATEGY", "basic"
    )  # 'basic', 'skip', 'retry'

    @classmethod
    def get_ai_provider_url(cls) -> str:
        """获取AI Provider服务URL"""
        return cls.AI_PROVIDER_URL

    @classmethod
    def get_ai_provider_timeout(cls) -> int:
        """获取AI Provider服务超时时间"""
        return cls.AI_PROVIDER_TIMEOUT

    @classmethod
    def is_ai_processing_enabled(cls) -> bool:
        """检查是否启用AI处理"""
        return cls.ENABLE_AI_PROCESSING

    @classmethod
    def get_fallback_strategy(cls) -> str:
        """获取回退策略"""
        return cls.AI_FALLBACK_STRATEGY
