"""TokenRecorder 全局 token 记录器"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseTokenRecorder(ABC):
    @abstractmethod
    def record_tokens(self, content_id, model_id, input_tokens, output_tokens):
        pass


class ConsoleTokenRecorder(BaseTokenRecorder):
    """测试用实现，打印到控制台。"""

    def record_tokens(self, content_id, model_id, input_tokens, output_tokens):
        # 打印到控制台
        print(
            f"[TokenRecorder] content_id={content_id}, model={model_id}, input_tokens={input_tokens}, output_tokens={output_tokens}"
        )