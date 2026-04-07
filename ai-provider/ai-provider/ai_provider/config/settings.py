"""Configuration settings for AI Provider."""

import os
import json
from dataclasses import dataclass
from pathlib import Path

current_dir = Path(__file__).parent
project_root = current_dir.parent.parent


@dataclass
class Credential:
    """Credential configuration for AWS Bedrock."""

    name: str
    access_key: str
    secret_key: str
    tokens_quota_per_minute: int
    requests_quota_per_minute: int
    weight: int


@dataclass
class BedrockConfig:
    """AWS Bedrock configuration for multimodal content processing."""

    region: str
    nova_pro_model_id: str
    nova_lite_model_id: str
    credentials: list[Credential]


@dataclass
class OpenAIConfig:
    """OpenAI configuration for text processing."""

    url: str
    token: str
    model: str
    traffic_ratio: float
    requests_quota_per_minute: int
    tokens_quota_per_minute: int


@dataclass
class AnthropicConfig:
    """Anthropic Claude configuration for text processing."""

    api_key: str
    base_url: str
    model: str
    traffic_ratio: float
    requests_quota_per_minute: int
    tokens_quota_per_minute: int


@dataclass
class FFmpegConfig:
    """FFmpeg configuration for video processing."""

    slice_video_duration: int
    max_video_size: int
    sample_frames: int


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str
    format: str
    enable_console: bool
    enable_file: bool
    file_path: str
    max_file_size: int
    backup_count: int


@dataclass
class ThreadPoolConfig:
    """Thread pool configuration."""

    text_executor_workers: int
    multimodal_executor_workers: int
    text_max_queue_size: int
    multimodal_max_queue_size: int


class Settings:
    """Main settings class for AI Provider."""

    def __init__(self):
        # Debug mode
        self.is_debug: bool = os.getenv("DEBUG", "0") == "1"

        # Server configuration
        self.server_port = int(os.getenv("SERVER_PORT", "8002"))

        # OpenAI configuration
        self.openai = OpenAIConfig(
            url=os.getenv("OPENAI_URL", "https://api.openai.com/v1/chat/completions"),
            token=os.getenv("OPENAI_TOKEN", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            traffic_ratio=float(os.getenv("OPENAI_TRAFFIC_RATIO", "0")),
            requests_quota_per_minute=int(
                os.getenv("OPENAI_REQUESTS_QUOTA_PER_MINUTE", "1000")
            ),
            tokens_quota_per_minute=int(
                os.getenv("OPENAI_TOKENS_QUOTA_PER_MINUTE", "1000000")
            ),
        )

        # Anthropic Claude configuration
        self.anthropic = AnthropicConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            base_url=os.getenv("ANTHROPIC_BASE_URL", ""),
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            traffic_ratio=float(os.getenv("ANTHROPIC_TRAFFIC_RATIO", "0")),
            requests_quota_per_minute=int(
                os.getenv("ANTHROPIC_REQUESTS_QUOTA_PER_MINUTE", "1000")
            ),
            tokens_quota_per_minute=int(
                os.getenv("ANTHROPIC_TOKENS_QUOTA_PER_MINUTE", "1000000")
            ),
        )

        # AWS Bedrock configuration (for multimodal content)
        self.bedrock = BedrockConfig(
            region=os.getenv("AWS_BEDROCK_REGION", "us-east-1"),
            nova_pro_model_id=os.getenv("AWS_BEDROCK_NOVA_PRO_MODEL_ID", "amazon.nova-pro-v1:0"),
            nova_lite_model_id=os.getenv("AWS_BEDROCK_NOVA_LITE_MODEL_ID", "amazon.nova-lite-v1:0"),
            credentials=self._load_bedrock_credentials(),
        )

        # FFmpeg configuration (for video processing)
        self.ffmpeg = FFmpegConfig(
            sample_frames=int(os.getenv("FFMPEG_SAMPLE_FRAMES", "10")),
            slice_video_duration=int(os.getenv("FFMPEG_SLICE_VIDEO_DURATION", "120")),
            max_video_size=int(os.getenv("FFMPEG_MAX_VIDEO_SIZE", "100")),
        )

        # Retry configuration
        self.retry_max_attempts = int(os.getenv("RETRY_MAX_ATTEMPTS", "1"))
        self.retry_wait_multiplier = int(os.getenv("RETRY_WAIT_MULTIPLIER", "1000"))

        # Logging configuration
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv(
                "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            enable_console=os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true",
            enable_file=os.getenv("LOG_ENABLE_FILE", "false").lower() == "true",
            file_path=os.getenv("LOG_FILE_PATH", "logs/app.log"),
            max_file_size=int(os.getenv("LOG_MAX_FILE_SIZE", "104857600")),  # 100MB
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        )

        # Thread pool workers configuration
        text_executor_workers = int(os.getenv("TEXT_EXECUTOR_WORKERS", "64"))
        multimodal_executor_workers = int(
            os.getenv("MULTIMODAL_EXECUTOR_WORKERS", "32")
        )
        text_max_queue_size = int(
            os.getenv("TEXT_MAX_QUEUE_SIZE", text_executor_workers * 2)
        )
        multimodal_max_queue_size = int(
            os.getenv("MULTIMODAL_MAX_QUEUE_SIZE", multimodal_executor_workers * 2)
        )

        self.threadpool = ThreadPoolConfig(
            text_executor_workers=text_executor_workers,
            multimodal_executor_workers=multimodal_executor_workers,
            text_max_queue_size=text_max_queue_size,
            multimodal_max_queue_size=multimodal_max_queue_size,
        )

    def _load_bedrock_credentials(self) -> list[Credential]:
        """Load Bedrock multi-account configuration."""
        credentials = []

        credentials_json = os.getenv("AWS_BEDROCK_CREDENTIALS", "aws-credentials.json")
        credentials_path = project_root / credentials_json

        if not credentials_path.exists():
            # Fall back to environment variables if no credentials file
            credentials.append(
                Credential(
                    name="default",
                    access_key=os.getenv("AWS_ACCESS_KEY_ID", ""),
                    secret_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                    tokens_quota_per_minute=1000000,
                    requests_quota_per_minute=1000,
                    weight=1,
                )
            )
            return credentials

        with open(credentials_path, "r") as f:
            credentials_data = json.load(f)

        try:
            for cred_data in credentials_data:
                credentials.append(
                    Credential(
                        name=cred_data.get("name", ""),
                        access_key=cred_data.get("access_key", ""),
                        secret_key=cred_data.get("secret_key", ""),
                        tokens_quota_per_minute=cred_data.get(
                            "tokens_quota_per_minute", 1000000
                        ),
                        requests_quota_per_minute=cred_data.get(
                            "requests_quota_per_minute", 1000
                        ),
                        weight=cred_data.get("weight", 1),
                    )
                )
        except json.JSONDecodeError:
            credentials.append(
                Credential(
                    name="default",
                    access_key=os.getenv("AWS_ACCESS_KEY_ID", ""),
                    secret_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                    tokens_quota_per_minute=1000000,
                    requests_quota_per_minute=1000,
                    weight=1,
                )
            )

        return credentials


# Global settings instance
global_settings = Settings()