"""Request models for LLM Proxy API endpoints."""


class InvalidRequestException(Exception):
    """无效请求异常"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
