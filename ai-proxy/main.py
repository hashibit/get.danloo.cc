"""FastAPI main application for AI Proxy service."""

import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import json
import base64
from cryptography.fernet import Fernet


# fmt: off
import os
from dotenv import load_dotenv
env_active = os.getenv("ENV_ACTIVE", "")
env_file = f".env.{env_active}" if env_active else ".env"
print(f"env_active: {env_active}, env_file: {env_file}")
load_dotenv(env_file)
# fmt: on

# Import shared models from common
from common.api_models.ai_provider import (
    ClassificationResult,
    ClassifyMaterialRequest,
    ClassifyMaterialResponse,
)

# OpenAI client no longer needed - using ai-provider service instead
# from openai_client import OpenAICompletion

# Import ObjectService from common
from common.object.services.object_service import ObjectService

# 配置日志
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 创建FastAPI应用
app = FastAPI(
    title="AI Proxy Service",
    description="Proxy service for AI processing with S3 integration",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 固定的加密密钥
FIXED_ENCRYPTION_KEY = b"fixed_encryption_key_32_bytes_long!!"

# 创建Fernet加密器
cipher_suite = Fernet(
    base64.urlsafe_b64encode(FIXED_ENCRYPTION_KEY.ljust(32, b"!")[:32])
)


# Initialize ObjectService from environment
try:
    object_service = ObjectService.from_env()
    classify_result_bucket = os.getenv("S3_RESULTS_BUCKET", "danloo-results")
    classify_result_object_service = ObjectService.from_env(
        bucket=classify_result_bucket
    )
except Exception as e:
    logger.error(f"Failed to initialize ObjectService: {e}")
    object_service = None
    classify_result_object_service = None

# OpenAI client no longer needed - using ai-provider service instead
# openai_client = OpenAICompletion()


def download_file_content(bucket: str, object_key: str) -> bytes:
    """Download file content from S3."""
    import tempfile
    import os

    if not object_service:
        raise HTTPException(status_code=500, detail="ObjectService not initialized")

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Download using ObjectService's s3_client directly
        object_service.s3_client.download_file(bucket, object_key, temp_path)

        # Read file content
        with open(temp_path, "rb") as f:
            content = f.read()

        return content

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def upload_file_content(bucket: str, object_key: str, content: bytes) -> bool:
    """Upload file content to S3."""
    import tempfile
    import os

    if not classify_result_object_service:
        raise HTTPException(
            status_code=500, detail="ClassifyResultObjectService not initialized"
        )

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Upload using ObjectService
        return classify_result_object_service.upload_file(bucket, object_key, temp_path)

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/classify-material")
async def classify_material(request: Dict[str, Any]):
    """处理材料分类请求"""
    try:
        logger.info("Received classification request")

        # 解密请求数据
        encrypted_data = request.get("data")
        if not encrypted_data:
            raise HTTPException(status_code=400, detail="Missing encrypted data")

        decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
        data = json.loads(decrypted_data.decode())

        # 获取S3文件信息
        object_bucket = data.get("object_bucket")
        object_key = data.get("object_key")
        if not object_bucket or not object_key:
            raise HTTPException(status_code=400, detail="Missing object bucket or key")

        # 从S3下载文件内容
        logger.info(f"Downloading file from S3: bucket={object_bucket}, key={object_key}")
        file_content = download_file_content(object_bucket, object_key)
        text_content = file_content.decode("utf-8", errors="ignore")

        # 获取 ai-provider 地址
        ai_provider_url = os.getenv("AI_PROVIDER_URL", "http://localhost:8002")
        logger.info(f"Calling ai-provider at {ai_provider_url}/api/classify-material")

        # 调用 ai-provider 的 classify-material 接口
        import httpx
        
        # 生成content_id
        content_id = str(hash(object_key) % 1000000)
        
        classify_request = {
            "content_id": content_id,
            "text_content": text_content
        }

        with httpx.Client(timeout=180) as client:
            response = client.post(
                f"{ai_provider_url}/api/classify-material",
                json=classify_request,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                logger.error(f"ai-provider classify-material failed: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"ai-provider classify-material failed: {response.text}",
                )

            ai_result = response.json()
            logger.info(f"ai-provider classification successful")

            # 提取 token 使用信息从响应头
            token_metadata = {}
            response_headers = response.headers
            if 'X-Token-Usage' in response_headers:
                # 解析 token usage header
                token_usage_str = response_headers['X-Token-Usage']
                logger.info(f"Token usage from ai-provider: {token_usage_str}")

                # 解析格式: {model_id:model1,input_tokens:100,output_tokens:50,request_path:/api/classify}
                try:
                    token_parts = {}
                    # 去掉花括号并分割
                    cleaned = token_usage_str.strip('{}').split('}{')[0]  # 如果有多个模型,取第一个
                    for part in cleaned.split(','):
                        if ':' in part:
                            key, value = part.split(':', 1)
                            token_parts[key.strip()] = value.strip()

                    input_tokens = int(token_parts.get('input_tokens', 0)) if token_parts.get('input_tokens') else 0
                    output_tokens = int(token_parts.get('output_tokens', 0)) if token_parts.get('output_tokens') else 0

                    token_metadata = {
                        "model": token_parts.get('model_id', 'unknown'),
                        "prompt_tokens": input_tokens,
                        "completion_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "finish_reason": None,  # X-Token-Usage header 不包含 finish_reason
                        "duration_seconds": 0.0  # ai-proxy 暂不记录duration
                    }
                    logger.info(f"Parsed token metadata: {token_metadata}")
                except Exception as e:
                    logger.error(f"Failed to parse token usage header: {e}")
                    token_metadata = {}

        # 转换ai-provider结果为简化格式
        try:
            # 提取知识点标题
            knowledge_points = []
            if "knowledge_points" in ai_result:
                for kp in ai_result["knowledge_points"]:
                    if isinstance(kp, dict) and "title" in kp:
                        knowledge_points.append(kp["title"])
                    elif isinstance(kp, str):
                        knowledge_points.append(kp)

            # 生成简化的摘要
            summary = ""
            if knowledge_points:
                summary = f"主要知识点包括：{', '.join(knowledge_points[:3])}"

            classify_result = {
                "knowledge_points": knowledge_points[:5],  # 最多5个知识点
                "language": ai_result.get("language", "zh-CN"),
                "summary": summary,
                "metadata": token_metadata if token_metadata else ai_result.get("llm_result", {}),  # 使用token metadata而不是llm_result
            }

        except (KeyError, TypeError) as e:
            logger.warning(
                f"Failed to parse ai-provider response: {e}, using default format"
            )
            classify_result = {
                "knowledge_points": ["分类处理完成"],
                "language": "zh-CN",
                "summary": "材料分类已完成",
                "metadata": {},
            }

        # 保存结果到S3的classify_result bucket
        result_key = os.path.splitext(object_key)[0] + ".classify_result.txt"
        result_content = json.dumps(classify_result)
        upload_file_content(classify_result_bucket, result_key, result_content.encode())

        # 加密响应数据
        response_data = {
            "result_bucket": classify_result_bucket,
            "result_key": result_key,
        }
        response_json = json.dumps(response_data)
        logger.info(f"classify response_json: {response_json}")
        encrypted_response = cipher_suite.encrypt(response_json.encode())

        return {"status": "success", "data": encrypted_response.decode()}

    except Exception as e:
        logger.error(f"Classification failed:", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/summary-pellet")
async def summary_pellet(request: Dict[str, Any]):
    """
    处理 Pellet 摘要生成请求

    请求格式（加密后）:
    {
        "summary_data_bucket": "bucket-name",
        "summary_data_key": "path/to/summary-data.json"
    }

    summary-data.json 格式:
    {
        "results": [...],  # ClassificationResult 列表
        "params": [...]    # MaterialContentData 列表
    }

    响应格式（加密后）:
    {
        "result_bucket": "bucket-name",
        "result_key": "path/to/pellet-result.json"
    }
    """
    try:
        logger.info("Received pellet summary request")

        # 解密请求数据
        encrypted_data = request.get("data")
        if not encrypted_data:
            raise HTTPException(status_code=400, detail="Missing encrypted data")

        decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
        data = json.loads(decrypted_data.decode())

        # 获取汇总数据的 S3 路径
        summary_data_bucket = data.get("summary_data_bucket")
        summary_data_key = data.get("summary_data_key")
        if not summary_data_bucket or not summary_data_key:
            raise HTTPException(
                status_code=400, detail="Missing summary data bucket or key"
            )

        logger.info(
            f"Downloading summary data from S3: bucket={summary_data_bucket}, key={summary_data_key}"
        )

        # 从 S3 下载汇总数据
        summary_data_content = download_file_content(
            summary_data_bucket, summary_data_key
        )
        summary_data = json.loads(summary_data_content.decode())

        # 获取 ai-provider 地址
        ai_provider_url = os.getenv("AI_PROVIDER_URL", "http://localhost:8002")
        logger.info(f"Calling ai-provider at {ai_provider_url}/api/summary-pellet")

        # 调用 ai-provider 的 summary-pellet 接口
        import httpx

        with httpx.Client(timeout=300) as client:
            response = client.post(
                f"{ai_provider_url}/api/summary-pellet",
                json=summary_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code != 200:
                logger.error(f"ai-provider summary-pellet failed: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"ai-provider summary-pellet failed: {response.text}",
                )

            pellet_results = response.json()
            logger.info(f"ai-provider returned {len(pellet_results)} pellets")

        # 保存结果到 S3
        result_key = summary_data_key.replace(".json", ".pellet_result.json")
        result_content = json.dumps(pellet_results)
        upload_file_content(classify_result_bucket, result_key, result_content.encode())

        # 加密响应数据
        response_data = {
            "result_bucket": classify_result_bucket,
            "result_key": result_key,
        }
        response_json = json.dumps(response_data)
        logger.info(f"pellet summary response_json: {response_json}")
        encrypted_response = cipher_suite.encrypt(response_json.encode())

        return {"status": "success", "data": encrypted_response.decode()}

    except Exception as e:
        logger.error(f"Pellet summary failed:", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=int(os.getenv("SERVER_PORT", "8091")),
            log_level="info",
            reload=False,
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Running in test mode...")
        # 在测试模式下，只打印信息
        print("AI Proxy Service")
        print(f"Would listen on port: {os.getenv('SERVER_PORT', '8091')}")
