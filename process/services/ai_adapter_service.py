"""
AI Adapter Service for integrating Process Service with AI Provider Service
"""

import httpx
import json
import os
import base64
from cryptography.fernet import Fernet
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from api_models.material_model import MaterialContentData
from common.api_models.ai_provider import (
    PelletPage,
    SuggestedTag,
    ClassificationResult,
    ExtractContentRequest,
    SummaryPelletRequest,
)
from process.database import SessionLocal
from common.database_models.token_usage_model import TokenUsageDB
from typing import Tuple, List

from config.ai_config import AIConfig

import logging

logger = logging.getLogger(__name__)


def parse_token_usage_to_records(
    request_uuid: str,
    consumer: str,
    token_usage: str,
) -> List[TokenUsageDB]:
    """
    Parse token usage string into database records

    Args:
        request_uuid: Request UUID from response header
        consumer: Consumer identifier (format: task:{task_id} or job:{job_id})
        token_usage: Token usage string from response header (format: {model_id:model1,input_tokens:100,output_tokens:50,request_path:/api/classify}{model_id:model2,...})

    Returns:
        list[TokenUsageDB]: List of token usage records ready to be saved to database
    """
    token_usage_records = []

    try:
        # Parse token usage from header - it may contain multiple models
        # Format: {model_id:model1,input_tokens:100,output_tokens:50,request_path:/api/classify}{model_id:model2,...}

        # Split by '}{' to get individual model usage blocks
        model_blocks = token_usage.strip('{}').split('}{')

        for block in model_blocks:
            # Parse each model block
            token_parts = {}
            for part in block.split(','):
                if ':' in part:
                    key, value = part.split(':', 1)
                    token_parts[key.strip()] = value.strip()

            # Extract model_id for this block
            block_model_id = token_parts.get('model_id')
            if not block_model_id:
                continue

            # Map the fields from the header format to our database schema
            prompt_tokens = int(token_parts.get('input_tokens', 0)) if token_parts.get('input_tokens') else None
            completion_tokens = int(token_parts.get('output_tokens', 0)) if token_parts.get('output_tokens') else None
            total_tokens = None
            if prompt_tokens is not None and completion_tokens is not None:
                total_tokens = prompt_tokens + completion_tokens

            # Create token usage record for each model
            token_usage_record = TokenUsageDB(
                request_uuid=request_uuid,
                consumer=consumer,
                model_id=block_model_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                input_cost=None,  # Not provided in current format
                output_cost=None,  # Not provided in current format
                total_cost=None,  # Not provided in current format
            )

            token_usage_records.append(token_usage_record)
            logger.info(f"Token usage record prepared: request_uuid={request_uuid}, consumer={consumer}, model_id={block_model_id}, total_tokens={total_tokens}")

    except Exception as e:
        logger.error(f"Failed to parse token usage: {str(e)}")
        logger.error(f"Token usage string was: {token_usage}")

    return token_usage_records


class AIAdapterService:
    """适配器服务，用于连接Process Service和AI Provider Service"""

    def __init__(self):
        # AI Provider服务配置
        self.ai_provider_url = AIConfig.get_ai_provider_url()
        self.ai_provider_timeout = AIConfig.get_ai_provider_timeout()
        
        # AI Proxy服务配置
        self.ai_proxy_url = os.getenv("AI_PROXY_URL", "http://ai-proxy:8091")
        
        # 加密配置（与ai-proxy一致）
        FIXED_ENCRYPTION_KEY = b'fixed_encryption_key_32_bytes_long!!'
        self.cipher_suite = Fernet(base64.urlsafe_b64encode(FIXED_ENCRYPTION_KEY.ljust(32, b'!')[:32]))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    def _make_http_request(self, endpoint: str, data: dict, consumer: str) -> tuple[dict, list[TokenUsageDB]]:
        """统一的HTTP请求方法"""
        full_url = f"{self.ai_provider_url}{endpoint}"
        logger.info(f"Calling AI Provider: {full_url}")
        logger.debug(f"Request data keys: {list(data.keys())}")

        try:
            with httpx.Client(timeout=self.ai_provider_timeout) as client:
                response = client.post(full_url, json=data)

                logger.info(f"AI Provider response: status={response.status_code}")

                # Extract and print response headers
                headers = response.headers
                logger.info("=== Response Headers ===")

                # Print standard headers
                if 'X-Request-UUID' in headers:
                    logger.info(f"Request UUID: {headers['X-Request-UUID']}")
                if 'X-Request-Duration' in headers:
                    logger.info(f"Request Duration: {headers['X-Request-Duration']}")
                if 'X-Request-Path' in headers:
                    logger.info(f"Request Path: {headers['X-Request-Path']}")
                if 'X-Service-Name' in headers:
                    logger.info(f"Service Name: {headers['X-Service-Name']}")

                token_usage_records = []

                # Print token usage headers
                if 'X-Token-Usage' in headers:
                    logger.info(f"Token Usage: {headers['X-Token-Usage']}")

                    # Parse token usage to records
                    request_uuid = headers.get('X-Request-UUID')
                    token_usage = headers.get('X-Token-Usage')

                    if request_uuid and token_usage:
                        # Use the consumer parameter passed to _make_http_request
                        token_usage_records = parse_token_usage_to_records(
                            request_uuid=request_uuid,
                            consumer=consumer,
                            token_usage=token_usage
                        )

                logger.info("======================")

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"AI Provider success response received")
                    logger.debug(
                        f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'list response'}"
                    )

                    return result, token_usage_records
                elif response.status_code == 429:
                    logger.warning(f"AI Provider rate limited: {response.text}")
                    raise httpx.TimeoutException("Rate limited by AI Provider")
                elif response.status_code >= 500:
                    logger.error(
                        f"AI Provider server error {response.status_code}: {response.text}"
                    )
                    raise httpx.ConnectError(
                        f"AI Provider server error: {response.status_code}"
                    )
                else:
                    logger.error(
                        f"AI Provider client error {response.status_code}: {response.text}"
                    )
                    raise Exception(
                        f"AI Provider client error: {response.status_code} - {response.text}"
                    )

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling AI Provider {full_url}: {str(e)}")
            raise
        except httpx.ConnectError as e:
            logger.error(f"Connection error calling AI Provider {full_url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling AI Provider {full_url}: {str(e)}")
            raise

    def classify_material(
        self,
        object_id: str,
        content_type: str,
        content_title: str,
        content_b64: str,
        consumer: str,
    ) -> Tuple[ClassificationResult, List[TokenUsageDB]]:
        """
        使用AI Provider处理对象内容（同步调用）

        Args:
            object_id: 对象ID
            content: 对象内容
                - 对于文本内容（text/*）：传入解码后的文本字符串
                - 对于二进制内容（image/*, video/*, audio/*, application/pdf）：传入base64编码字符串
            content_type: 内容类型，支持以下类型：
                - text/*: 文本文件（如 text/plain, text/html, text/markdown）
                - image/*: 图像文件（如 image/jpeg, image/png, image/gif）
                - video/*: 视频文件（如 video/mp4, video/avi, video/mov）
                - audio/*: 音频文件（如 audio/mp3, audio/wav, audio/aac）
                - application/pdf: PDF文档
            material_title: 材料标题（可选）

        Returns:
            包含AI处理结果的字典，包括：
            - object_id: 对象ID
            - result_data: 处理结果数据（JSON字符串）
            - result_type: 结果类型
            - ai_result: 原始AI处理结果
        """
        logger.info(
            f"Classifying material: object_id={object_id}, content_type={content_type}"
        )
        logger.info(f"Material title: {content_title}")
        logger.debug(f"Content length: {len(content_b64)} characters")

        try:
            # 根据内容类型准备AI Provider请求
            request_data = self._prepare_materials_extract_request(
                object_id,
                content_type,
                content_title,
                content_b64,
            )

            logger.debug(f"Prepared request for material classification")

            result_data, token_usage_records = self._make_http_request(
                "/api/extract-content", request_data.model_dump(), consumer
            )

            result = ClassificationResult(**result_data)
            logger.info(
                f"Material classification successful: {len(result.knowledge_points)} knowledge points extracted"
            )
            logger.debug(f"Classification language: {result.language}")

            return result, token_usage_records

        except Exception as e:
            logger.error(f"Error processing object {object_id} with AI: {str(e)}")
            raise e

    def _prepare_materials_extract_request(
        self,
        object_id: str,
        content_type: str,
        content_title: str,
        content_64: str,
    ) -> ExtractContentRequest:
        """
        准备AI Provider请求数据

        Args:
            object_id: 对象ID
            content: 对象内容
            content_type: 内容类型
            material_title: 材料标题

        Returns:
            ExtractContentRequest对象
        """
        # 根据内容类型处理 - 文本用text_content，其他用object_content_base64
        if content_type.startswith("text/"):
            # 文本内容使用text_content字段
            return ExtractContentRequest(
                content_id=object_id,
                text_content=content_64,
                extras={
                    "material_title": content_title,
                    "content_type": content_type,
                    "object_id": object_id,
                },
            )
        else:
            # 非文本内容（image, video, audio, pdf）都使用object_content_base64
            return ExtractContentRequest(
                content_id=object_id,
                object_content_base64=content_64,
                object_content_type=content_type,
                extras={
                    "material_title": content_title,
                    "content_type": content_type,
                    "object_id": object_id,
                },
            )

    def summarize_materials_to_pellets(
        self, results: List[ClassificationResult], params: List[MaterialContentData], consumer: str
    ) -> Tuple[List[PelletPage], List[TokenUsageDB]]:
        """
        调用AI Provider的SummaryPellet接口生成pellet

        Args:
            results: 材料处理结果列表

        Returns:
            list[PelletPage]: 包含pellet内容、评分和标签的摘要结果列表
        """
        logger.info(
            f"Generating pellet summaries from {len(results)} classification results"
        )

        # 统计knowledge points
        total_knowledge_points = sum(len(result.knowledge_points) for result in results)
        logger.info(f"Total knowledge points to summarize: {total_knowledge_points}")

        try:
            # 构建请求数据
            request = SummaryPelletRequest(results=results, params=params)
            logger.debug("Prepared SummaryPelletRequest")

            result_data, token_usage_records = self._make_http_request(
                "/api/summary-pellet", request.model_dump(), consumer
            )

            logger.info(f"/summary-pellet get result_data: {result_data}")

            # AI Provider现在返回List[PelletPage]
            pellets = [
                PelletPage(**pellet_data) for pellet_data in result_data
            ]

            logger.info(f"Successfully generated {len(pellets)} pellet summaries")
            for i, pellet in enumerate(pellets, 1):
                logger.info(
                    f"Pellet {i}: title='{pellet.title}', score={pellet.score}, tags_count={len(pellet.tags)}"
                )

            return pellets, token_usage_records

        except Exception as e:
            logger.error(f"Error calling AI Provider SummaryPellet: {str(e)}")
            raise  # 重新抛出异常,让调用方处理失败情况

    def classify_material_via_proxy(self, object_bucket: str, object_key: str) -> dict:
        """
        通过AI Proxy服务进行材料分类

        Args:
            object_bucket: S3存储桶名称
            object_key: S3对象键名

        Returns:
            dict: 包含result_bucket和result_key的响应数据
        """
        logger.info(f"Calling AI Proxy for material classification: bucket={object_bucket}, key={object_key}")

        try:
            # 准备请求数据
            request_data = {
                "object_bucket": object_bucket,
                "object_key": object_key,
            }

            # 加密请求数据
            request_json = json.dumps(request_data)
            encrypted_request = self.cipher_suite.encrypt(request_json.encode())

            # 调用ai-proxy服务
            ai_proxy_endpoint = f"{self.ai_proxy_url}/api/classify-material"
            logger.info(f"Calling ai-proxy service: {ai_proxy_endpoint}")

            with httpx.Client(timeout=240) as client:
                payload = {
                    "data": encrypted_request.decode()
                }

                response = client.post(
                    ai_proxy_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    logger.error(f"AI proxy service failed: {response.text}")
                    raise Exception(f"AI proxy service failed: {response.text}")

                response_data = response.json()
                encrypted_result = response_data.get("data")
                if not encrypted_result:
                    raise Exception("Missing encrypted result from ai-proxy response")

                # 解密响应数据
                decrypted_result = self.cipher_suite.decrypt(encrypted_result.encode())
                result_data = json.loads(decrypted_result.decode())

                # 验证结果数据
                result_bucket = result_data.get("result_bucket")
                result_key = result_data.get("result_key")

                if not result_bucket or not result_key:
                    raise Exception("Missing result bucket or key from ai-proxy response")

                logger.info(f"AI Proxy classification successful: result_bucket={result_bucket}, result_key={result_key}")
                return result_data

        except Exception as e:
            logger.error(f"Error calling AI Proxy service: {str(e)}")
            raise

    def summarize_materials_to_pellets_via_proxy(
        self,
        summary_data_bucket: str,
        summary_data_key: str
    ) -> Tuple[List[PelletPage], List[TokenUsageDB]]:
        """
        通过 AI Proxy 服务生成 pellet 摘要

        Args:
            summary_data_bucket: S3 存储桶名称（包含汇总数据）
            summary_data_key: S3 对象键名（汇总数据文件路径）

        Returns:
            Tuple[List[PelletPage], List[TokenUsageDB]]: pellet 摘要列表和 token 使用记录
        """
        logger.info(f"Calling AI Proxy for pellet summary: bucket={summary_data_bucket}, key={summary_data_key}")

        try:
            # 准备请求数据
            request_data = {
                "summary_data_bucket": summary_data_bucket,
                "summary_data_key": summary_data_key,
            }

            # 加密请求数据
            request_json = json.dumps(request_data)
            encrypted_request = self.cipher_suite.encrypt(request_json.encode())

            # 调用 ai-proxy 服务
            ai_proxy_endpoint = f"{self.ai_proxy_url}/api/summary-pellet"
            logger.info(f"Calling ai-proxy service: {ai_proxy_endpoint}")

            with httpx.Client(timeout=360) as client:  # 更长的超时时间，因为需要生成多篇文章
                payload = {
                    "data": encrypted_request.decode()
                }

                response = client.post(
                    ai_proxy_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    logger.error(f"AI proxy summary-pellet failed: {response.text}")
                    raise Exception(f"AI proxy summary-pellet failed: {response.text}")

                response_data = response.json()
                encrypted_result = response_data.get("data")
                if not encrypted_result:
                    raise Exception("Missing encrypted result from ai-proxy response")

                # 解密响应数据
                decrypted_result = self.cipher_suite.decrypt(encrypted_result.encode())
                result_data = json.loads(decrypted_result.decode())

                # 验证结果数据
                result_bucket = result_data.get("result_bucket")
                result_key = result_data.get("result_key")

                if not result_bucket or not result_key:
                    raise Exception("Missing result bucket or key from ai-proxy response")

                logger.info(f"AI Proxy returned pellet result at: bucket={result_bucket}, key={result_key}")

                # 从 S3 下载 pellet 结果
                from .material_content_service import material_content_service
                pellet_result_content = material_content_service.read_file_from_s3(
                    bucket=result_bucket,
                    key=result_key
                )

                pellet_data = json.loads(pellet_result_content)

                # 解析为 PelletPage 对象
                pellets = [
                    PelletPage(**pellet_item) for pellet_item in pellet_data
                ]

                logger.info(f"Successfully loaded {len(pellets)} pellet summaries from ai-proxy")

                # ai-proxy 不返回 token usage，返回空列表
                return pellets, []

        except Exception as e:
            logger.error(f"Error calling AI Proxy summary-pellet: {str(e)}")
            raise  # 重新抛出异常,让调用方处理失败情况
