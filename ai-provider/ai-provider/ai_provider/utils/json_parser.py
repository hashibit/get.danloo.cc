"""JSON parsing utilities."""

import json
import logging
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class JsonParser:
    """JSON parsing utilities class."""

    @staticmethod
    def try_find_json_object_string(input_string: str) -> str | None:
        """尝试从字符串中找到JSON对象"""
        if not input_string:
            return None

        # 寻找第一个 { 和最后一个 }
        start = input_string.find("{")
        end = input_string.rfind("}")

        if start == -1 or end == -1 or start >= end:
            return None

        return input_string[start : end + 1]

    @staticmethod
    def try_find_json_array_string(input_string: str) -> str | None:
        """尝试从字符串中找到JSON数组"""
        if not input_string:
            return None

        # 寻找第一个 [ 和最后一个 ]
        start = input_string.find("[")
        end = input_string.rfind("]")

        if start == -1 or end == -1 or start >= end:
            return None

        return input_string[start : end + 1]

    @staticmethod
    def fix_wrong_escapes(json_string: str) -> str:
        """修复JSON字符串中的错误转义"""
        if not json_string:
            return json_string

        # 修复常见的转义问题
        json_string = json_string.replace('\\"', '"')
        json_string = json_string.replace("\\n", "\n")
        json_string = json_string.replace("\\t", "\t")
        json_string = json_string.replace("\\r", "\r")

        return json_string

    @staticmethod
    def is_valid_json(json_string: str) -> bool:
        """检查字符串是否是有效的JSON"""
        try:
            json.loads(json_string)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    @staticmethod
    def try_deserialize(json_string: str, target_class: type[T]) -> T | None:
        """尝试反序列化JSON字符串到指定类型"""
        try:
            data = json.loads(json_string)
            if hasattr(target_class, "parse_obj"):
                # Pydantic model
                return target_class.parse_obj(data)
            elif hasattr(target_class, "model_validate"):
                # Pydantic v2 model
                return target_class.model_validate(data)
            else:
                # 普通类
                return target_class(**data)
        except Exception as e:
            logger.error(
                f"Failed to deserialize JSON ( {json_string} ) to {target_class.__name__}: {e}"
            )
            return None

    @staticmethod
    def try_deserialize_to_dict(json_string: str) -> dict | None:
        """尝试反序列化JSON字符串到字典"""
        try:
            return json.loads(json_string)
        except Exception as e:
            logger.error(f"Failed to deserialize JSON ( {json_string} ) to dict: {e}")
            return None
