"""Rate limiter implementation for LLM requests."""

import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RequestRecord:
    """请求记录"""

    timestamp: float
    input_tokens: int
    output_tokens: int


@dataclass
class RateLimiterState:
    """速率限制器状态"""

    queue_size: int
    tokens_count: int  # 以万为单位
    requests_count: int


class RateLimiter:
    """速率限制器 - 基于滑动窗口的令牌桶算法"""

    def __init__(
        self,
        name: str,
        tokens_per_minute: int = 1000000,  # 每分钟token数
        requests_per_minute: int = 1000,  # 每分钟请求数
        tokens_upper_limit: Optional[int] = None,  # token上限水位
        requests_upper_limit: Optional[int] = None,  # 请求上限水位
        tokens_safe_level: Optional[int] = None,  # token安全水位
        requests_safe_level: Optional[int] = None,  # 请求安全水位
        window_seconds: int = 60,  # 滑动窗口大小（秒）
    ):
        self.name = name
        self.tokens_per_minute = tokens_per_minute
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds

        # 设置水位线
        self.tokens_upper_limit = tokens_upper_limit or int(tokens_per_minute * 0.9)
        self.requests_upper_limit = requests_upper_limit or int(
            requests_per_minute * 0.9
        )
        self.tokens_safe_level = tokens_safe_level or int(tokens_per_minute * 0.7)
        self.requests_safe_level = requests_safe_level or int(requests_per_minute * 0.7)

        # 滑动窗口记录
        self.request_records = deque()
        self.tokens_counter = 0
        self.requests_counter = 0

        # 线程锁
        self.lock = threading.Lock()

    def _clean_window_records(self):
        """清理滑动窗口外的记录"""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        while self.request_records and self.request_records[0].timestamp < cutoff_time:
            old_record = self.request_records.popleft()
            # 从计数器中减去过期记录的值（只计算input tokens，与record_request保持一致）
            self.tokens_counter -= old_record.input_tokens
            self.requests_counter -= 1

        # 防止计数器变成负数（可能由于之前的不一致导致）
        if self.tokens_counter < 0 or self.requests_counter < 0:
            logger.warning(
                f"RateLimiter {self.name}: counter inconsistency detected, recalculating from records"
            )
            self._recalculate_counters()

    def _recalculate_counters(self):
        """重新计算计数器（基于当前的记录）"""
        self.tokens_counter = sum(
            record.input_tokens for record in self.request_records
        )
        self.requests_counter = len(self.request_records)
        logger.info(
            f"RateLimiter {self.name}: recalculated counters - tokens: {self.tokens_counter}, requests: {self.requests_counter}"
        )

    def has_free_tokens_and_requests(self) -> bool:
        """检查是否有空闲的token和请求额度"""
        return (
            self.tokens_counter < self.tokens_upper_limit
            and self.requests_counter < self.requests_upper_limit
        )

    def has_enough_tokens_and_requests(self) -> bool:
        """检查是否有足够的token和请求额度（安全水位）"""
        return (
            self.tokens_counter < self.tokens_safe_level
            and self.requests_counter < self.requests_safe_level
        )

    def wait_for_tokens_and_requests(self):
        """等待令牌和请求额度 - 实现降水逻辑"""
        with self.lock:
            # 先清理过期记录
            self._clean_window_records()

            # 如果水位过高，进入降水周期
            if not self.has_free_tokens_and_requests():
                logger.info(f"[水位过高] {self.name} - 进入降水周期")

                while not self.has_enough_tokens_and_requests():
                    logger.info(
                        f"[降水中] {self.name} - "
                        f"Tokens: {self.tokens_counter}/{self.tokens_per_minute}, "
                        f"Requests: {self.requests_counter}/{self.requests_per_minute}"
                    )
                    # 释放锁，等待5秒后重新检查
                    self.lock.release()
                    time.sleep(5)
                    self.lock.acquire()
                    self._clean_window_records()

                logger.info(
                    f"[水位安全] {self.name} - "
                    f"Tokens: {self.tokens_counter}/{self.tokens_per_minute}, "
                    f"Requests: {self.requests_counter}/{self.requests_per_minute}"
                )

    def record_request(self, input_tokens: int = 0, output_tokens: int = 0):
        """记录请求"""
        with self.lock:
            # 先清理过期记录
            self._clean_window_records()

            # 添加新记录
            record = RequestRecord(
                timestamp=time.time(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            self.request_records.append(record)

            # 更新计数器（只计算input tokens，与Java版本一致）
            self.tokens_counter += input_tokens
            self.requests_counter += 1

    def get_rate_limiter_state(self) -> RateLimiterState:
        """获取速率限制器状态"""
        with self.lock:
            self._clean_window_records()

            return RateLimiterState(
                queue_size=len(self.request_records),
                tokens_count=self.tokens_counter // 10000,  # 转换为万
                requests_count=self.requests_counter,
            )

    def print_state(self) -> str:
        """打印状态信息"""
        state = self.get_rate_limiter_state()
        return (
            f"Name: {self.name}, Records: {state.queue_size}, "
            f"Tokens: {state.tokens_count}万, Requests: {state.requests_count}"
        )