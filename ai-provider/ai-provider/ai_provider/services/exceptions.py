"""Custom exceptions for LLM services."""


class BedrockCallException(Exception):
    """Bedrock调用异常"""

    pass


class BedrockInvalidRequestException(BedrockCallException):
    """Bedrock调用异常 客户端"""

    pass
