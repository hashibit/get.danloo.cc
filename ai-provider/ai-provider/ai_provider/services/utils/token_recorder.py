"""TokenRecorder 全局 token 记录器"""

from abc import ABC, abstractmethod
import logging
from common.utils.request_context import add_token_usage

logger = logging.getLogger(__name__)


class BaseTokenRecorder(ABC):
    @abstractmethod
    def record_tokens(self, content_id, model_id, input_tokens, output_tokens):
        pass


class DBTokenRecorder(BaseTokenRecorder):
    """默认实现，记录到数据库。"""

    def __init__(self, data_ai_log_mapper):
        self.data_ai_log_mapper = data_ai_log_mapper

    def record_tokens(self, content_id, model_id, input_tokens, output_tokens):
        # 这里假设 data_ai_log_mapper 有 insert 方法，参数与 Java 类似
        log = {
            "content_id": content_id,
            "type": "TOKEN_COUNT",
            "input_token_count": input_tokens,
            "output_token_count": output_tokens,
            "model": model_id,
        }
        self.data_ai_log_mapper.insert(log)


class ConsoleTokenRecorder(BaseTokenRecorder):
    """测试用实现，打印到控制台并记录到请求上下文。"""

    def record_tokens(self, content_id, model_id, input_tokens, output_tokens):
        # 记录到请求上下文 - 现在model_id是必需的
        add_token_usage(input_tokens, output_tokens, model_id)

        # 打印到控制台
        print(
            f"[TokenRecorder] content_id={content_id}, model={model_id}, input_tokens={input_tokens}, output_tokens={output_tokens}"
        )
