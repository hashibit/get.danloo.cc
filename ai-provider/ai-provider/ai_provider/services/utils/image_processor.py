import base64
import io
import logging
import urllib3
import requests
from PIL import Image

# 禁用SSL警告（仅在测试环境中使用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ImageProcessor:
    """图片处理工具类，负责图片下载、格式识别和转换等功能"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_size = 10 * 1024 * 1024  # 10MB限制
        self.connect_timeout = 10  # 10秒连接超时
        self.read_timeout = 30  # 30秒读取超时

    class ImageData:
        """图片数据包装类，包含图片格式和字节数据"""

        def __init__(self, format: str, data: bytes):
            self.format = format
            self.data = data

        def get_format(self) -> str:
            return self.format

        def get_data(self) -> bytes:
            return self.data

    def load_image_from_url(self, image_url: str) -> ImageData:
        """
        从URL加载图片数据

        Args:
            image_url: 图片URL

        Returns:
            ImageData: 图片数据对象，包含格式和字节数组

        Raises:
            RuntimeError: 无法加载网络图片时抛出异常
        """
        try:
            # 设置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # 发送请求
            response = requests.get(
                image_url,
                headers=headers,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=True,
            )
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get("content-type", "")
            if not content_type:
                content_type = ""

            # 检查内容长度
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                raise ValueError(f"图片太大: {content_length} bytes")

            # 读取原始图片数据
            original_image_data = b""
            total_bytes = 0

            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    original_image_data += chunk
                    total_bytes += len(chunk)
                    if total_bytes > self.max_size:
                        raise ValueError("图片下载过程中超过大小限制")

            # 检测原始格式
            source_format = self._detect_image_format_from_bytes(original_image_data)
            if source_format == "unknown":
                source_format = self._detect_image_format_from_content_type(
                    content_type, image_url
                )

            # 确定目标格式
            target_format = self._determine_target_format(source_format)

            # 如果需要转换格式
            if source_format != target_format:
                try:
                    converted_data = self._convert_image_format(
                        original_image_data, target_format
                    )
                    return self.ImageData(target_format, converted_data)
                except Exception as e:
                    self.logger.warning(
                        f"图片格式转换失败 {source_format} -> {target_format}, 使用原始格式: {e}"
                    )
                    return self.ImageData(source_format, original_image_data)

            return self.ImageData(source_format, original_image_data)

        except Exception as e:
            self.logger.error(f"网络图片下载失败: {image_url}", exc_info=True)
            raise RuntimeError(f"无法加载网络图片: {image_url}") from e

    def _detect_image_format_from_bytes(self, image_data: bytes) -> str:
        """
        从字节数据检测图片格式

        Args:
            image_data: 图片字节数据

        Returns:
            str: 图片格式
        """
        if not image_data or len(image_data) < 8:
            return "unknown"

        # 首先尝试使用 PIL 检测格式
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                return img.format.lower() if img.format else "unknown"
        except Exception:
            pass

        # 手动检测常见格式
        # PNG: 89 50 4E 47 0D 0A 1A 0A
        if (
            len(image_data) >= 8
            and image_data[0] == 0x89
            and image_data[1] == 0x50
            and image_data[2] == 0x4E
            and image_data[3] == 0x47
            and image_data[4] == 0x0D
            and image_data[5] == 0x0A
            and image_data[6] == 0x1A
            and image_data[7] == 0x0A
        ):
            return "png"

        # JPEG: FF D8 FF
        if (
            len(image_data) >= 3
            and image_data[0] == 0xFF
            and image_data[1] == 0xD8
            and image_data[2] == 0xFF
        ):
            return "jpeg"

        # GIF: "GIF87a" or "GIF89a"
        if (
            len(image_data) >= 6
            and image_data[0] == ord("G")
            and image_data[1] == ord("I")
            and image_data[2] == ord("F")
            and image_data[3] == ord("8")
            and image_data[4] in (ord("7"), ord("9"))
            and image_data[5] == ord("a")
        ):
            return "gif"

        # WebP: "RIFF" + "WEBP"
        if (
            len(image_data) >= 12
            and image_data[0] == ord("R")
            and image_data[1] == ord("I")
            and image_data[2] == ord("F")
            and image_data[3] == ord("F")
            and image_data[8] == ord("W")
            and image_data[9] == ord("E")
            and image_data[10] == ord("B")
            and image_data[11] == ord("P")
        ):
            return "webp"

        # BMP: "BM"
        if (
            len(image_data) >= 2
            and image_data[0] == ord("B")
            and image_data[1] == ord("M")
        ):
            return "bmp"

        return "unknown"

    def _detect_image_format_from_content_type(
        self, content_type: str, image_url: str
    ) -> str:
        """
        从Content-Type和URL检测图片格式

        Args:
            content_type: HTTP Content-Type
            image_url: 图片URL

        Returns:
            str: 图片格式
        """
        format_type = "jpeg"  # 默认格式

        # 从Content-Type判断
        content_type_lower = content_type.lower()
        if "png" in content_type_lower:
            format_type = "png"
        elif "jpeg" in content_type_lower or "jpg" in content_type_lower:
            format_type = "jpeg"
        elif "gif" in content_type_lower:
            format_type = "gif"
        elif "bmp" in content_type_lower:
            format_type = "bmp"
        elif "webp" in content_type_lower:
            format_type = "webp"
        elif "tiff" in content_type_lower or "tif" in content_type_lower:
            format_type = "tiff"
        elif "svg" in content_type_lower:
            format_type = "svg"
        elif "heic" in content_type_lower or "heif" in content_type_lower:
            format_type = "heic"
        elif "avif" in content_type_lower:
            format_type = "avif"
        elif "jfif" in content_type_lower:
            format_type = "jpeg"

        # 从URL路径判断，当Content-Type不准确时作为备选
        lower_url = image_url.lower()
        if lower_url.endswith(".png"):
            format_type = "png"
        elif lower_url.endswith((".jpg", ".jpeg", ".jfif")):
            format_type = "jpeg"
        elif lower_url.endswith(".gif"):
            format_type = "gif"
        elif lower_url.endswith(".bmp"):
            format_type = "bmp"
        elif lower_url.endswith(".webp"):
            format_type = "webp"
        elif lower_url.endswith((".tiff", ".tif")):
            format_type = "tiff"
        elif lower_url.endswith(".svg"):
            format_type = "svg"
        elif lower_url.endswith((".heic", ".heif")):
            format_type = "heic"
        elif lower_url.endswith(".avif"):
            format_type = "avif"

        return format_type

    def _determine_target_format(self, source_format: str) -> str:
        """
        确定目标格式（AWS Bedrock支持的格式）

        Args:
            source_format: 原始格式

        Returns:
            str: 目标格式
        """
        # AWS Bedrock主要支持jpeg和png格式
        if source_format == "png":
            return "png"
        elif source_format == "jpeg":
            return "jpeg"
        else:
            # 其他格式统一转为jpeg
            return "jpeg"

    def _convert_image_format(self, image_data: bytes, target_format: str) -> bytes:
        """
        转换图片格式

        Args:
            image_data: 原始图片数据
            target_format: 目标格式

        Returns:
            bytes: 转换后的图片数据

        Raises:
            ValueError: 转换失败时抛出异常
        """
        try:
            # 使用PIL读取图片
            image = Image.open(io.BytesIO(image_data))

            # 如果是RGBA格式且目标格式是JPEG，需要转换为RGB
            if target_format.lower() == "jpeg" and image.mode in ("RGBA", "LA", "P"):
                # 创建白色背景
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background

            # 转换格式
            output_buffer = io.BytesIO()

            # 根据目标格式设置保存参数
            save_kwargs = {}
            if target_format.lower() == "jpeg":
                save_kwargs["quality"] = 95
                save_kwargs["optimize"] = True
            elif target_format.lower() == "png":
                save_kwargs["optimize"] = True

            image.save(output_buffer, format=target_format.upper(), **save_kwargs)
            return output_buffer.getvalue()

        except Exception as e:
            raise ValueError(f"图片格式转换失败: {e}") from e

    def url_to_base64(self, image_url: str) -> str:
        """
        从URL下载图片并转换为base64字符串

        Args:
            image_url: 图片URL

        Returns:
            str: base64编码的图片数据
        """
        image_data = self.load_image_from_url(image_url)
        return base64.b64encode(image_data.get_data()).decode("utf-8")

    def get_image_info(self, image_url: str) -> tuple[str, int]:
        """
        获取图片格式和大小信息

        Args:
            image_url: 图片URL

        Returns:
            tuple[str, int]: (格式, 大小字节数)
        """
        image_data = self.load_image_from_url(image_url)
        return image_data.get_format(), len(image_data.get_data())
