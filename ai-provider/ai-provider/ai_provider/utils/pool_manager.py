import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, Executor, Future
from typing import Callable, Any
from ai_provider.config.settings import global_settings
from ai_provider.utils.logging_config import setup_logging


class BoundedThreadPoolExecutor(Executor):
    """有界队列的线程池执行器 - 继承 Executor 接口"""

    def __init__(self, max_workers, max_queue_size, thread_name_prefix=""):
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix=thread_name_prefix
        )
        self.max_queue_size = max_queue_size
        self.pending_tasks = 0
        self.logger = setup_logging(global_settings.logging).getChild(
            "BoundedThreadPool"
        )
        self._queue_lock = threading.Lock()  # 使用threading.Lock而不是asyncio.Lock

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future[Any]:
        """伪装成标准 ThreadPoolExecutor.submit 接口"""
        # 使用线程锁确保原子操作
        with self._queue_lock:
            # 检查当前负载（同步检查）
            if self.pending_tasks >= self.max_queue_size:
                self.logger.warning(
                    f"线程池队列已满，拒绝任务。当前排队任务: {self.pending_tasks}/{self.max_queue_size}"
                )
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=503,
                    detail=f"服务繁忙，请稍后重试。当前排队任务: {self.pending_tasks}/{self.max_queue_size}",
                )

            # 在提交任务前增加计数
            self.pending_tasks += 1
            self.logger.debug(
                f"任务提交到线程池，当前排队任务: {self.pending_tasks}/{self.max_queue_size}"
            )

        # 包装原始函数，添加计数器
        def wrapped_fn(*args, **kwargs):
            try:
                self.logger.debug(
                    f"任务开始执行，当前排队任务: {self.pending_tasks}/{self.max_queue_size}"
                )
                result = fn(*args, **kwargs)
                return result
            finally:
                # 任务完成后减少计数
                with self._queue_lock:
                    self.pending_tasks -= 1
                    self.logger.debug(
                        f"任务执行完成，当前排队任务: {self.pending_tasks}/{self.max_queue_size}"
                    )

        # 委托给真正的 ThreadPoolExecutor
        return self.executor.submit(wrapped_fn, *args, **kwargs)

    def shutdown(self, *args, **kwargs) -> None:
        """关闭线程池 - 自动转发所有参数"""
        return self.executor.shutdown(*args, **kwargs)

    @property
    def _max_workers(self):
        """兼容属性"""
        return self.executor._max_workers

    @property
    def _threads(self):
        """兼容属性"""
        return self.executor._threads


class ThreadPoolManager:
    text_executor: BoundedThreadPoolExecutor
    multimodal_executor: BoundedThreadPoolExecutor

    def __init__(self):

        # 快速操作线程池（轻量任务，队列稍大）
        self.text_executor = BoundedThreadPoolExecutor(
            max_workers=global_settings.threadpool.text_executor_workers,
            max_queue_size=global_settings.threadpool.text_max_queue_size,
            thread_name_prefix="light_task",
        )

        # 重型操作线程池（使用有界队列的线程池）
        self.multimodal_executor = BoundedThreadPoolExecutor(
            max_workers=global_settings.threadpool.multimodal_executor_workers,
            max_queue_size=global_settings.threadpool.multimodal_max_queue_size,
            thread_name_prefix="heavy_task",
        )


pool_manager = ThreadPoolManager()
