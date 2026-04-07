import base64
import logging
import os
from datetime import datetime
import shutil
import subprocess
import tempfile
import time
from common.utils.ulid_utils import generate_ulid
import urllib3
import requests
import ffmpeg
from functools import wraps

from retrying import retry
from ai_provider.config.settings import global_settings
from .ffmpeg_errors import is_ffmpeg_slice_error_retryable

# 禁用SSL警告（仅在测试环境中使用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class FFmpegException(Exception):
    """FFmpeg执行异常"""

    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message

    def __str__(self) -> str:
        if self.original_exception:
            return f"{self.message}. 原因: {str(self.original_exception)}"
        return self.message


class VideoProcessor:
    """视频处理工具类，负责视频下载、格式检查、帧提取等功能"""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.sample_frames = global_settings.ffmpeg.sample_frames  # 默认提取10帧
        # 默认120s
        self.max_video_slice_duration = global_settings.ffmpeg.slice_video_duration
        # 100MB限制
        self.max_size = global_settings.ffmpeg.max_video_size * 1024 * 1024

        self.connect_timeout = 60  # 30秒连接超时
        self.read_timeout = 120  # 60秒读取超时

    def sample_video_frames_b64(self, content_id: int, video_url: str) -> list[str]:
        frames = self.sample_video_frames(content_id, video_url)
        return [base64.b64encode(frame).decode("utf-8") for frame in frames]

    def sample_video_frames(self, content_id: int, video_url: str) -> list[bytes]:
        """
        从视频中提取帧并返回字节数组列表

        Args:
            content_id: 内容ID
            video_url: 视频URL

        Returns:
            list[bytes]: 帧的字节数组列表

        Raises:
            Exception: 视频处理失败时抛出异常
        """
        try:
            logger.info(f"Content ID: {content_id} 开始提取视频帧: {video_url}")

            # 检查视频合法性
            self.ffprobe_check(content_id, video_url)

            # 提取帧
            frames = self._sample_video_frames(video_url)

            logger.info(f"Content ID: {content_id} 成功提取 {len(frames)} 帧")
            return frames

        except Exception as e:
            logger.error(f"Content ID: {content_id} 提取视频帧失败: {e}")
            raise

    def _sample_video_frames(self, video_url: str) -> list[bytes]:
        """
        从视频中提取帧并返回字节数组列表

        Args:
            video_url: 视频URL

        Returns:
            list[bytes]: 帧的字节数组列表
        """
        try:
            logger.debug(f"视频文件：{video_url}")

            frames = []

            # 使用ffmpeg-python提取帧
            probe = ffmpeg.probe(video_url)
            video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")

            # 获取视频时长（秒）
            duration = float(video_info.get("duration", 0))
            if duration <= 0:
                # 如果无法获取时长，使用默认值
                duration = 30

            # 计算帧间隔（秒）
            frame_interval = max(
                1.0, duration / (self.sample_frames * 3)
            )  # 先提取3倍帧数

            # 提取帧
            for i in range(self.sample_frames * 3):
                timestamp = i * frame_interval
                if timestamp >= duration:
                    break

                try:
                    # 使用ffmpeg提取指定时间点的帧
                    frame_data = (
                        ffmpeg.input(video_url, ss=timestamp)
                        .output("pipe:", vframes=1, format="image2", vcodec="mjpeg")
                        .run(capture_stdout=True, quiet=True)
                    )[0]

                    if frame_data and len(frame_data) > 0:
                        frames.append(frame_data)

                except Exception as e:
                    logger.warning(f"提取第 {i+1} 帧失败: {e}")
                    continue

            # 如果提取的帧数超过目标数量，进行采样
            if len(frames) > self.sample_frames:
                step = len(frames) // self.sample_frames
                frames = [frames[i] for i in range(0, len(frames), step)][
                    : self.sample_frames
                ]

            return frames

        except Exception as e:
            logger.error(f"提取视频帧失败: {e}")
            raise

    def ffprobe_check(self, content_id: int, video_url: str) -> None:
        """
        验证视频文件的完整性

        Args:
            content_id: 内容ID
            video_url: 视频URL

        Raises:
            FFmpegException: 视频检查失败时抛出异常
        """
        try:
            logger.debug(f"Content ID: {content_id} 开始检查视频: {video_url}")

            # 使用ffmpeg-python检查视频
            probe = ffmpeg.probe(video_url)

            # 检查是否有视频流
            video_streams = [s for s in probe["streams"] if s["codec_type"] == "video"]
            if not video_streams:
                raise FFmpegException("视频流不存在")

            video_info = video_streams[0]

            # 检查基本信息
            if "codec_name" not in video_info:
                raise FFmpegException("视频编码信息缺失")

            # 检查分辨率
            width = video_info.get("width", 0)
            height = video_info.get("height", 0)
            if width <= 0 or height <= 0:
                raise FFmpegException(f"无效的分辨率: {width} x {height}")

            # 检查时长
            duration = float(video_info.get("duration", 0))
            if duration <= 0.1:  # 100ms以下的内容
                raise FFmpegException("视频时长太短")

            # 检查帧率
            frame_rate = video_info.get("r_frame_rate", "0/1")
            if frame_rate == "0/1":
                logger.warning(f"Content ID: {content_id} 无法获取有效帧率，但继续处理")
                # 不抛出异常，因为某些视频可能没有帧率信息但仍然可以处理

            logger.debug(f"Content ID: {content_id} 视频检查通过")

        except FFmpegException:
            # 如果已经是FFmpegException，直接抛出
            raise
        except Exception as e:
            logger.error(f"Content ID: {content_id} 视频检查失败: {e}")
            raise FFmpegException(f"视频检查失败: {str(e)}", e)

    def download_video_to_bytes(
        self,
        content_id: int,
        video_url: str,
        slice_duration: int | None = None,
        max_size: int | None = None,
    ) -> bytes:
        """
        切片视频片段

        Args:
            content_id: 内容ID
            video_url: 视频URL
            slice_duration: 切片时长，单位为秒，默认切片 max_video_slice_duration 秒。如果传0表示不切片
            max_size: 最大视频大小，单位为字节，默认使用类属性max_size
        Returns:
            bytes: 切片后的视频字节数据

        Raises:
            Exception: 视频切片失败时抛出异常
        """
        if slice_duration is None:
            slice_duration = self.max_video_slice_duration
        try:
            logger.info(f"Content ID: {content_id} 开始切片视频: {video_url}")

            # 检查视频合法性
            self.ffprobe_check(content_id, video_url)

            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=True, suffix=".mp4") as tmp_file:
                output_path = tmp_file.name

                if slice_duration <= 0:
                    # 下载视频，不切片
                    self.download_video_to_file(video_url, output_path)
                else:
                    # 执行切片
                    self.ffmpeg_slice(
                        content_id, video_url, output_path, slice_duration, max_size
                    )
                    # 验证输出文件
                    if not self.validate_output_file(output_path):
                        raise Exception("视频切片不正确")

                    logger.info(f"Content ID: {content_id} 视频切片成功: {output_path}")

                # debug_filename = f"{content_id}_video_slice_{datetime.now()}.mp4"
                # shutil.copyfile(output_path, debug_filename)

                # 视频文件不会很大
                with open(output_path, "rb") as f:
                    return f.read()

        except Exception as e:
            import traceback

            traceback.print_exc()
            logger.error(f"Content ID: {content_id} 视频切片失败: {e}")
            raise

    @retry(
        stop_max_attempt_number=3,
        wait_exponential_multiplier=1000,
        retry_on_exception=is_ffmpeg_slice_error_retryable,
    )
    def ffmpeg_slice(
        self,
        content_id: int,
        input_url: str,
        output_path: str,
        duration: int | None = None,
        max_size: int | None = None,
    ) -> None:
        """
        使用FFmpeg切片视频

        Args:
            content_id: 内容ID
            input_url: 输入视频URL
            output_path: 输出文件路径
            duration: 切片时长，单位为秒，默认切片 max_video_slice_duration 秒
            max_size: 最大视频大小，单位为字节，默认使用类属性max_size
        Raises:
            Exception: FFmpeg执行失败时抛出异常
        """
        try:
            # 使用传入的参数或默认值
            duration = duration or self.max_video_slice_duration
            max_size = max_size or self.max_size

            # 构建FFmpeg命令 - 限制最大分辨率为480p，帧率不超过30fps，使用高压缩参数，确保尺寸为2的倍数
            # min(960,iw)：如果原视频宽度 > 960，缩放到 960；如果 ≤ 960，保持原宽度
            # min(540,ih)：如果原视频高度 > 540，缩放到 540；如果 ≤ 540，保持原高度
            #
            # 对于小视频（比如 480x360），不会强制放大到 960x540
            # 对于大视频（比如 1920x1080），会缩放到 960x540
            # 对于竖屏视频（比如 1080x1920），会缩放到 540x960

            # 构建缩放滤镜：确保输出尺寸为偶数，避免FFmpeg编码错误
            # scale_filter = "scale='trunc(min(960,iw)/2)*2:trunc(min(540,ih)/2)*2'"
            # fps_filter = "fps=30"
            # video_filter = f"{scale_filter},{fps_filter}"

            # 540 x 960
            video_filter = "scale='min(540,iw*960/ih):min(960,ih*540/iw)':force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0"

            command = [
                self.ffmpeg_path,
                "-threads",
                "2",  # 全局限制线程数为2
                "-ss",
                "00:00:01",  # 从1秒开始
                "-t",
                str(duration),  # 截取指定秒数
                "-i",
                input_url,
                "-y",  # 覆盖输出文件
                "-vf",
                video_filter,
                "-c:v",
                "libx264",  # 使用H.264编码
                "-preset",
                "veryfast",  # 快速，因为通常来说，输入的视频已经是 h264 了
                "-x264opts",
                "threads=2",  # 专门限制x264编码器线程数
                "-crf",
                "28",  # 中等压缩比，保证质量
                "-r",
                "25",  # fps: 25
                "-fs",
                str(max_size),  # 硬限制文件大小（字节）
                "-profile:v",
                "baseline",  # 使用baseline profile，兼容性更好
                "-level",
                "3.0",  # 限制编码级别
                "-pix_fmt",
                "yuv420p",  # 确保像素格式兼容
                "-c:a",
                "aac",  # 音频转码为AAC
                "-b:a",
                "64k",  # 低音频比特率
                "-ar",
                "22050",  # 低音频采样率
                # "-an",   # 去掉音频
                output_path,
            ]

            logger.info(f"Content ID: {content_id} 执行FFmpeg命令: {' '.join(command)}")
            logger.info(
                f"Content ID: {content_id} 文件大小限制: {max_size} bytes ({max_size/(1024*1024):.1f} MB)"
            )

            # 执行命令
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=120  # 2分钟超时
            )

            if result.returncode != 0:
                raise FFmpegException(
                    f"FFmpeg执行失败，错误码: {result.returncode}, 错误信息: {result.stderr}"
                )

            # 检查输出文件大小
            if os.path.exists(output_path):
                actual_size = os.path.getsize(output_path)
                logger.info(
                    f"Content ID: {content_id} 输出文件大小: {actual_size} bytes ({actual_size/(1024*1024):.2f} MB)"
                )

            logger.debug(f"Content ID: {content_id} FFmpeg执行成功")

        except subprocess.TimeoutExpired as e:
            raise FFmpegException("FFmpeg执行超时", e)
        except FFmpegException:
            # 如果已经是FFmpegException，直接抛出
            raise
        except Exception as e:
            logger.error(f"Content ID: {content_id} FFmpeg执行失败: {e}")
            raise FFmpegException(f"FFmpeg执行失败: {str(e)}", e)

    def validate_output_file(self, file_path: str) -> bool:
        """
        验证输出文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件是否有效
        """
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0

    def download_video_to_file(self, video_url: str, save_path: str) -> None:
        """
        下载视频文件

        Args:
            video_url: 视频URL
            save_path: 保存路径

        Raises:
            Exception: 下载失败时抛出异常
        """
        try:
            logger.info(f"开始下载视频文件: {video_url}")

            # 设置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # 发送请求
            logger.info(
                f"发送HTTP请求，超时设置: 连接={self.connect_timeout}s, 读取={self.read_timeout}s"
            )
            response = requests.get(
                video_url,
                headers=headers,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=True,
                verify=False,  # 禁用SSL验证，避免证书问题
            )

            logger.info(f"HTTP响应状态: {response.status_code}")
            response.raise_for_status()

            # 检查内容长度
            content_length = response.headers.get("content-length")
            if content_length:
                logger.info(f"视频文件大小: {content_length} bytes")
                if int(content_length) > self.max_size:
                    raise ValueError(f"视频文件太大: {content_length} bytes")

            # 写入文件
            logger.info(f"开始写入文件: {save_path}")
            with open(save_path, "wb") as f:
                total_bytes = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)
                        if total_bytes > self.max_size:
                            raise ValueError("视频下载过程中超过大小限制")

            logger.info(f"视频文件下载完成: {save_path}, 总大小: {total_bytes} bytes")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误 - 无法连接到视频服务器: {video_url}, 错误: {e}")
            raise ConnectionError(f"无法连接到视频服务器: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"超时错误 - 下载视频超时: {video_url}, 错误: {e}")
            raise TimeoutError(f"下载视频超时: {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP错误 - 视频下载HTTP错误: {video_url}, 状态码: {e.response.status_code}, 错误: {e}"
            )
            raise Exception(f"视频下载HTTP错误: {e}")
        except Exception as e:
            logger.error(
                f"下载视频文件失败: {video_url}, 错误类型: {type(e).__name__}, 错误: {e}"
            )
            raise

    def dump_video_to_file(self, video_data_b64: str) -> str:
        filename = f"{generate_ulid()}.mp4"
        with open(filename, "wb") as f:
            f.write(base64.b64decode(video_data_b64))
        return filename

    def video_url_to_base64(
        self,
        content_id: int,
        video_url: str,
        slice_duration: int | None = None,
        max_size: int | None = None,
    ) -> str:
        """
        将视频URL转换为base64字符串。

        Args:
            content_id: 内容ID
            video_url: 视频URL
            slice_duration: 切片时长，单位为秒，默认切片 max_video_slice_duration 秒。如果传0表示不切片
            max_size: 最大视频大小，单位为字节，默认使用类属性max_size

        Returns:
            str: base64编码的视频数据
        """
        video_data = self.download_video_to_bytes(
            content_id, video_url, slice_duration=slice_duration, max_size=max_size
        )

        return base64.b64encode(video_data).decode("utf-8")

    def get_video_info(self, content_id: int, video_url: str) -> dict:
        """
        获取视频信息

        Args:
            video_url: 视频URL

        Returns:
            dict: 视频信息
        """
        try:
            probe = ffmpeg.probe(video_url)
            video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
            format_info = probe.get("format", {})

            # 获取比特率信息
            bitrate = 0
            if "bit_rate" in video_info:
                bitrate = int(video_info["bit_rate"])
            elif "bit_rate" in format_info:
                bitrate = int(format_info["bit_rate"])

            return {
                "duration": float(video_info.get("duration", 0)),
                "width": int(video_info.get("width", 0)),
                "height": int(video_info.get("height", 0)),
                "frame_rate": video_info.get("r_frame_rate", "0/1"),
                "codec": video_info.get("codec_name", "unknown"),
                "format": format_info.get("format_name", "unknown"),
                "bitrate": bitrate,
            }

        except Exception as e:
            logger.error(f"{content_id} 获取视频信息失败: {e}")
            # 返回默认值而不是抛出异常
            return {
                "duration": 0.0,
                "width": 0,
                "height": 0,
                "frame_rate": "0/1",
                "codec": "unknown",
                "format": "unknown",
                "bitrate": 0,
            }
