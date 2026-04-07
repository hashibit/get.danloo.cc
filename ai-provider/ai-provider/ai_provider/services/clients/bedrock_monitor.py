"""Bedrock client monitoring."""

import logging
import os
import threading
import time
from typing import List

logger = logging.getLogger(__name__)


class BedrockMonitor:
    """Bedrock客户端监控器"""

    def __init__(self, clients: List, stats_interval: int = None):
        """
        初始化监控器

        Args:
            clients: BedrockClient列表
            stats_interval: 统计间隔（毫秒），如果为None则从环境变量获取
        """
        self.clients = clients
        self.monitor_thread = None
        self.stop_monitoring = False

        # 从环境变量获取监控间隔，默认10秒
        if stats_interval is None:
            stats_interval = int(os.getenv("STATS_INTERVAL", "10000"))
        self.stats_interval = stats_interval / 1000  # 转换为秒

    def start_monitoring(self):
        """启动监控线程"""
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.stop_monitoring = False
            self.monitor_thread = threading.Thread(
                target=self._monitor_clients, daemon=True
            )
            self.monitor_thread.start()
            logger.info("BedrockMonitor监控线程已启动")

    def stop_monitor(self):
        """停止监控线程"""
        self.stop_monitoring = True
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
            logger.info("BedrockMonitor监控线程已停止")

    def _monitor_clients(self):
        """监控客户端状态的线程函数"""
        while not self.stop_monitoring:
            try:
                self._log_clients_stats()
                time.sleep(self.stats_interval)
            except Exception as e:
                logger.error(f"监控BedrockClient状态时出错: {e}")
                time.sleep(self.stats_interval)

    def _log_clients_stats(self):
        """打印客户端统计信息"""
        if not self.clients:
            return

        # 计算最大名称长度用于对齐
        max_name_length = max(len(client.name) for client in self.clients)

        for client in self.clients:
            state = client.rate_limiter.get_rate_limiter_state()
            padded_name = f"{client.name:<{max_name_length}}"
            padded_tokens = f"{state.tokens_count:3d}"
            logger.info(
                f"统计 BedrockClient: {padded_name}, tokens: {padded_tokens}万, requests: {state.requests_count}"
            )

    def get_clients_summary(self) -> dict:
        """获取客户端统计摘要"""
        if not self.clients:
            return {"total_clients": 0, "total_tokens": 0, "total_requests": 0}

        total_tokens = 0
        total_requests = 0

        for client in self.clients:
            state = client.rate_limiter.get_rate_limiter_state()
            total_tokens += state.tokens_count
            total_requests += state.requests_count

        return {
            "total_clients": len(self.clients),
            "total_tokens": total_tokens,
            "total_requests": total_requests,
        }
