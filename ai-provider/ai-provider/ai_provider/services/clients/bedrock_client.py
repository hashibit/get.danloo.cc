"""Bedrock client implementation."""

import json
import logging
import threading
from typing import Any
import boto3
from ...config import global_settings
from ...utils import RateLimiter, JsonParser
from ..exceptions import BedrockCallException
from ..utils.token_recorder import ConsoleTokenRecorder
from ..utils.image_processor import ImageProcessor
from ..utils.video_processor import VideoProcessor

logger = logging.getLogger(__name__)

inference_config = {
    "max_new_tokens": 1024,
    "temperature": 0.1,
    "top_p": 0.5,
}


class BedrockClient:
    """Bedrock客户端"""

    def __init__(self, credential, token_recorder=None):
        self.credential = credential
        self.name = credential.name
        try:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=global_settings.bedrock.region,
                aws_access_key_id=credential.access_key,
                aws_secret_access_key=credential.secret_key,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock client: {e}")
            self.client = None

        self.rate_limiter = RateLimiter(
            name=f"Bedrock-{self.name}",
            tokens_per_minute=credential.tokens_quota_per_minute,
            requests_per_minute=credential.requests_quota_per_minute,
            window_seconds=60,
        )

        # 信号量控制并发请求数，对应 Java 版本的 Semaphore(40)
        self.bedrock_request_semaphore = threading.Semaphore(40)

        # 记录 token
        self.token_recorder = token_recorder or ConsoleTokenRecorder()

        # 初始化图片和视频处理器
        self.image_processor = ImageProcessor()
        self.video_processor = VideoProcessor()

    def invoke_model(self, content_id: int, prompt: str, text: str) -> str:
        """
        调用Bedrock模型，输出是普通字符串，没有必要一定是 JSON 格式
        """

        if not self.client:
            raise BedrockCallException("Bedrock client not initialized")

        logger.info(f"Content ID: {content_id} 调用Bedrock客户端: {self.name}")

        # 等待速率限制
        self.rate_limiter.wait_for_tokens_and_requests()

        try:
            # 获取信号量
            self.bedrock_request_semaphore.acquire()

            # 构建请求。根据请求的模型，这个 body 不一样。下面这个写法是 Nova 的。
            # https://github.com/aws-samples/amazon-bedrock-samples/blob/main/introduction-to-bedrock/bedrock_apis/01_invoke_api.ipynb

            body = {
                "messages": [
                    {"role": "user", "content": [{"text": f"{prompt}\n\n{text}"}]}
                ],
                "schemaVersion": "messages-v1",
                "inferenceConfig": inference_config,
            }

            model_id = global_settings.bedrock.nova_lite_model_id

            try:
                response = self.client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                )

                result = json.loads(response["body"].read())
                content = (
                    result.get("output").get("message").get("content")[0].get("text")
                )

                # 记录使用情况
                usage = result.get("usage", {})
                inputTokens = usage.get("inputTokens", 0)
                outputTokens = usage.get("outputTokens", 0)
                totalTokens = usage.get("totalTokens", 0)
                cacheReadInputTokenCount = usage.get("cacheReadInputTokenCount", 0)
                cacheWriteInputTokenCount = usage.get("cacheWriteInputTokenCount", 0)

                self.rate_limiter.record_request(inputTokens, outputTokens)
                self.token_recorder.record_tokens(
                    content_id,
                    model_id,
                    inputTokens,
                    outputTokens,
                )

                logger.info(
                    f"Content ID: {content_id}, Bedrock模型 输入 Token: {inputTokens} 输出 Token: {outputTokens}"
                )

                return content

            except Exception as e:
                logger.error(f"Content ID: {content_id}, Bedrock调用失败: {e}")
                raise BedrockCallException(
                    f"Content ID: {content_id}, Bedrock调用失败: {e}"
                )

        finally:
            # 释放信号量
            self.bedrock_request_semaphore.release()

    def analyze_video(
        self,
        content_id: int,
        prompt: str,
        s3_video_slice_uri: str | None = None,
        s3_bucket_owner: str | None = None,
        video_data_b64: str | None = None,
        image_frames_b64: list[str] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> str:
        """分析视频，输出是 JSON 格式"""

        if not self.client:
            raise BedrockCallException("Bedrock client not initialized")

        logger.info(f"Content ID: {content_id} 调用Bedrock分析视频内容")

        # 等待速率限制
        self.rate_limiter.wait_for_tokens_and_requests()

        try:
            # 获取信号量
            self.bedrock_request_semaphore.acquire()

            # 构建多模态请求
            content_parts = []

            # 添加图片帧
            if image_frames_b64:
                for frame_b64 in image_frames_b64:
                    content_parts.append(
                        {
                            "image": {
                                "format": "jpeg",
                                "source": {
                                    "bytes": frame_b64,
                                },
                            },
                        }
                    )

            elif video_data_b64:
                content_parts.append(
                    {
                        "video": {
                            "format": "mp4",
                            "source": {
                                "bytes": video_data_b64,
                            },
                        }
                    }
                )

            elif s3_video_slice_uri:
                content_parts.append(
                    {
                        "video": {
                            "format": "mp4",
                            "source": {
                                "s3Location": {
                                    "uri": s3_video_slice_uri,
                                    "bucketOwner": s3_bucket_owner,
                                }
                            },
                        }
                    }
                )

            if extras:
                logger.info(f"Content ID: {content_id}, extras: {extras}: 暂未用到！")

            # 添加文本prompt
            content_parts.append({"text": prompt})

            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": content_parts,
                    }
                ],
                "schemaVersion": "messages-v1",
                "inferenceConfig": inference_config,
            }

            logger.debug(
                f"Content ID: {content_id}, 发送给Bedrock的请求: {json.dumps(body, indent=2)}"
            )

            try:

                response = self.client.invoke_model(
                    modelId=global_settings.bedrock.nova_pro_model_id,
                    body=json.dumps(body),
                )

                result = json.loads(response["body"].read())
                content = (
                    result.get("output").get("message").get("content")[0].get("text")
                )

                # 记录使用情况
                usage = result.get("usage", {})
                inputTokens = usage.get("inputTokens", 0)
                outputTokens = usage.get("outputTokens", 0)
                totalTokens = usage.get("totalTokens", 0)
                cacheReadInputTokenCount = usage.get("cacheReadInputTokenCount", 0)
                cacheWriteInputTokenCount = usage.get("cacheWriteInputTokenCount", 0)

                self.rate_limiter.record_request(inputTokens, outputTokens)
                self.token_recorder.record_tokens(
                    content_id,
                    global_settings.bedrock.nova_pro_model_id,
                    inputTokens,
                    outputTokens,
                )

                logger.info(
                    f"Content ID: {content_id}, Bedrock视频分析 输入 Token: {inputTokens} 输出 Token: {outputTokens}"
                )

                logger.debug(f"Content ID: {content_id}, Bedrock原始响应: {content}")

                json_string = JsonParser.try_find_json_object_string(content)
                if not json_string:
                    raise BedrockCallException(f"无法从响应中提取JSON: {content}")

                logger.info(f"Content ID: {content_id}, 提取的JSON: {json_string}")
                return JsonParser.fix_wrong_escapes(json_string)

            except Exception as e:
                logger.error(f"{content_id} Bedrock视频分析失败: {e}")
                raise BedrockCallException(
                    f"Content ID: {content_id}, Bedrock视频分析失败: {e}"
                )

        finally:
            # 释放信号量
            self.bedrock_request_semaphore.release()
