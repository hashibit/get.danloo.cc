import re
import logging
from enum import Enum
from typing import List

logger = logging.getLogger(__name__)


class FFmpegErrorType(Enum):
    """FFmpeg错误类型枚举"""

    NETWORK = "network"  # 网络相关错误
    TEMPORARY = "temporary"  # 临时性错误
    FILE_CORRUPTION = "corruption"  # 文件损坏
    ENCODING = "encoding"  # 编码问题
    UNKNOWN = "unknown"  # 未知错误


def is_ffmpeg_slice_error_retryable(exception):
    """判断是否为可重试的异常"""
    if not isinstance(exception, Exception):
        return False

    error_message = str(exception).lower()
    error_type = _determine_ffmpeg_error_type(error_message)

    # 只有网络和临时性错误可以重试
    retryable = error_type in [FFmpegErrorType.NETWORK, FFmpegErrorType.TEMPORARY]

    if retryable:
        logger.warning(
            f"ffmpeg slice got retryable error ({error_type.value}): {error_message}. will retry later"
        )
    else:
        logger.error(
            f"ffmpeg slice got non-retryable error ({error_type.value}): {error_message}"
        )

    return retryable


def _determine_ffmpeg_error_type(error_message: str) -> FFmpegErrorType:
    """确定FFmpeg错误类型"""

    # 网络相关错误模式
    network_patterns = [
        r"connection reset by peer",
        r"network is unreachable",
        r"connection refused",
        r"timeout",
        r"connection timed out",
        r"no route to host",
        r"host unreachable",
    ]

    # 临时性错误模式
    temporary_patterns = [
        r"reached eof",
        r"corrupted ctts atom",
        r"error reading header",
        r"error opening input",
        r"temporary failure",
        r"resource temporarily unavailable",
        r"input/output error",
        r"device or resource busy",
    ]

    # 文件损坏错误模式
    corruption_patterns = [
        r"non-existing pps",
        r"decode_slice_header error",
        r"no frame!",
        r"illegal reordering_of_pic_nums_idc",
        r"illegal modification_of_pic_nums_idc",
        r"illegal memory management control operation",
        r"reference count overflow",
        r"left block unavailable",
        r"top block unavailable",
        r"error while decoding mb",
        r"concealing",
        r"missing reference picture",
        r"co located pocs unavailable",
        r"invalid data found when processing input",
        r"file is truncated",
        r"invalid stream",
    ]

    # 编码问题错误模式
    encoding_patterns = [
        r"reserved bit set",
        r"number of bands exceeds limit",
        r"channel element.*not allocated",
        r"prediction is not allowed in aac-lc",
        r"slice type.*too large",
        r"deblocking filter parameters.*out of range",
        r"chroma_log2_weight_denom.*out of range",
        r"luma_log2_weight_denom.*out of range",
        r"reference overflow",
        r"invalid band type",
        r"gain control is not implemented",
        r"pulse tool not allowed",
        r"sample rate index.*does not match",
        r"decode_pce: input buffer exhausted",
        r"skip_data_stream_element: input buffer exhausted",
        r"could not open encoder",
        r"task finished with error code",
        r"nothing was written into output file",
        r"conversion failed",
        r"invalid argument",
        r"error submitting packet to decoder",
        r"invalid data found",
        r"terminating thread with return code",
        r"at least one of its streams received no packets",
        r"frame=.*fps=.*q=.*Lsize=.*time=N/A",
    ]

    # 检查错误类型 - 调整顺序，让更具体的错误类型优先匹配
    if _matches_patterns(error_message, encoding_patterns):
        return FFmpegErrorType.ENCODING
    elif _matches_patterns(error_message, corruption_patterns):
        return FFmpegErrorType.FILE_CORRUPTION
    elif _matches_patterns(error_message, network_patterns):
        return FFmpegErrorType.NETWORK
    elif _matches_patterns(error_message, temporary_patterns):
        return FFmpegErrorType.TEMPORARY
    else:
        return FFmpegErrorType.UNKNOWN


def _matches_patterns(text: str, patterns: List[str]) -> bool:
    """检查文本是否匹配任一模式"""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
