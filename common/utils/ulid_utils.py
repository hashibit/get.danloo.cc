"""
ULID 工具函数模块

使用 python-ulid 库生成 ULID (Universally Unique Lexicographically Sortable Identifier)
ULID 相比 UUID 的优势:
1. 字典序可排序 - 按时间顺序生成的 ULID 可以直接按字符串排序
2. 更短的字符串表示 - 26个字符 vs UUID的36个字符
3. URL 安全 - 使用 Crockford's base32 编码
4. 包含时间戳 - 前48位是毫秒级时间戳
"""

from ulid import ULID


def generate_ulid() -> str:
    """
    生成一个新的 ULID 字符串

    Returns:
        str: 26个字符的 ULID 字符串，例如: "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    Example:
        >>> ulid_str = generate_ulid()
        >>> len(ulid_str)
        26
    """
    return str(ULID())


def generate_ulid_from_timestamp(timestamp_ms: int) -> str:
    """
    从指定的时间戳生成 ULID

    Args:
        timestamp_ms: 毫秒级时间戳

    Returns:
        str: ULID 字符串
    """
    return str(ULID.from_timestamp(timestamp_ms / 1000.0))
