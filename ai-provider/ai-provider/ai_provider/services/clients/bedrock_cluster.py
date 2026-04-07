"""Bedrock cluster management."""

import logging
import random
from typing import Any
from ...config import global_settings
from .bedrock_client import BedrockClient
from .bedrock_monitor import BedrockMonitor
from ..exceptions import BedrockCallException

logger = logging.getLogger(__name__)


class BedrockCluster:
    """Bedrock集群管理"""

    def __init__(self):
        self.clients = []
        self.weighted_client_indexes = []

        # 初始化客户端
        for i, credential in enumerate(global_settings.bedrock.credentials):
            client = BedrockClient(credential)
            self.clients.append(client)

            # 根据权重添加到索引列表
            for _ in range(credential.weight):
                self.weighted_client_indexes.append(i)

        # 初始化并启动监控器
        self.monitor = BedrockMonitor(self.clients)
        self.monitor.start_monitoring()

    def choose_client(self) -> BedrockClient:
        """选择客户端（带权重的随机选择）"""
        if not self.weighted_client_indexes:
            raise BedrockCallException("没有可用的Bedrock客户端")

        rand_index = random.randint(0, len(self.weighted_client_indexes) - 1)
        client_index = self.weighted_client_indexes[rand_index]
        return self.clients[client_index]

    def invoke_model(self, content_id: int, prompt: str, text: str) -> str:
        """调用模型"""
        client = self.choose_client()
        logger.info(f"Content ID: {content_id} 选择Bedrock客户端: {client.name}")
        return client.invoke_model(content_id, prompt, text)

    def analyze_video(
        self,
        content_id: int,
        prompt: str,
        s3_video_slice_uri: str | None = None,
        s3_bucket_owner: str | None = None,
        video_data_b64: str | None = None,
        image_frames_b64: list[str] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> str:
        """分析视频"""
        client = self.choose_client()
        logger.info(f"Content ID: {content_id} 选择Bedrock客户端: {client.name}")
        return client.analyze_video(
            content_id,
            prompt,
            s3_video_slice_uri,
            s3_bucket_owner,
            video_data_b64,
            image_frames_b64,
            extras,
        )
