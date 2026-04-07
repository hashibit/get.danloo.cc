"""FastAPI main application using modular ai_provider."""

# fmt: off
import os
from dotenv import load_dotenv
load_dotenv()
# fmt: on

import uvicorn
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from ai_provider.utils.pool_manager import pool_manager
from ai_provider.utils.decorators import (
    handle_api_exceptions,
    execute_llm_operation,
    auto_set_content_id,
)
from common.middleware import setup_middleware
from ai_provider.utils.logging_config import setup_logging
from ai_provider import (
    global_settings,
    llm_caller,
)


# Import shared models from common
from common.api_models.ai_provider import ExtractContentRequest, SummaryPelletRequest
from common.api_models.ai_provider import (
    ClassificationResult,
    PelletPage,
)


# 配置日志
logger = setup_logging(global_settings.logging)

# 创建FastAPI应用
app = FastAPI(
    title="AI Provider Service",
    description="AI内容 - 模块化版本",
    version="2.0.0",
    # 优化响应时间和并发处理
    timeout=30,  # 默认超时30秒
)

# Setup common middleware
setup_middleware(app, "ai-provider")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/extract-content", response_model=ClassificationResult)
@handle_api_exceptions
@auto_set_content_id
async def extract_content(request: ExtractContentRequest):
    """统一的内容提取接口，支持文本和图片和视频"""
    logger.info(f"Content extraction request received: content_id={request.content_id}")

    # 记录请求详情（不记录完整内容，只记录摘要）
    if request.text_content:
        logger.info(f"Text content length: {len(request.text_content)} characters")
    if request.object_content_base64:
        logger.info(
            f"Object content type: {request.object_content_type}, base64 length: {len(request.object_content_base64)}"
        )
    if request.http_video_url:
        logger.info(f"Video URL provided: {request.http_video_url}")
    if request.http_image_urls:
        logger.info(f"Image URLs count: {len(request.http_image_urls)}")
    if request.extras:
        logger.debug(f"Extras keys: {list(request.extras.keys())}")

    try:
        result = await execute_llm_operation(
            pool_manager.multimodal_executor,
            llm_caller.extract_content,
            request.content_id,
            request.text_content,
            request.http_video_url,
            request.http_image_urls,
            request.object_content_base64,
            request.object_content_type,
            request.extras,
        )

        logger.info(
            f"Content extraction successful: content_id={request.content_id}, knowledge_points={len(result.knowledge_points)}"
        )
        logger.debug(f"Extracted language: {result.language}")

        return result

    except Exception as e:
        logger.error(
            f"Content extraction failed: content_id={request.content_id}, error={str(e)}"
        )
        raise


@app.post("/api/classify-material", response_model=ClassificationResult)
@handle_api_exceptions
@auto_set_content_id
async def classify_material(request: ExtractContentRequest):
    """材料分类接口，基于文本内容进行知识点提取"""
    logger.info(f"Material classification request: content_id={request.content_id}")

    try:
        # Use the existing extract_content logic
        result = await execute_llm_operation(
            pool_manager.multimodal_executor,
            llm_caller.extract_content,
            request.content_id,
            request.text_content,
            request.http_video_url,
            request.http_image_urls,
            request.object_content_base64,
            request.object_content_type,
            request.extras,
        )

        logger.info(
            f"Material classification successful: content_id={request.content_id}, knowledge_points={len(result.knowledge_points)}"
        )

        return result

    except Exception as e:
        logger.error(
            f"Material classification failed: content_id={request.content_id}, error={str(e)}"
        )
        raise


@app.post("/api/summary-pellet", response_model=List[PelletPage])
@handle_api_exceptions
async def summary_pellet(request: SummaryPelletRequest):
    """生成Pellet摘要接口，基于多个材料处理结果生成统一摘要"""
    logger.info(
        f"Pellet summary request received: {len(request.results)} classification results"
    )

    # 统计输入数据
    total_knowledge_points = sum(
        len(result.knowledge_points) for result in request.results
    )
    languages = set(result.language for result in request.results if result.language)

    logger.info(
        f"Input summary: {total_knowledge_points} total knowledge points, languages: {languages}"
    )

    # 占位
    content_id = 0

    try:
        result = await execute_llm_operation(
            pool_manager.multimodal_executor,
            llm_caller.summary_pellet,
            content_id,
            request.results,
            request.params,
        )

        logger.info(
            f"Pellet summary generation successful: {len(result)} pellets generated"
        )

        # 记录生成的pellets摘要
        for i, pellet in enumerate(result, 1):
            logger.info(
                f"Generated pellet {i}: title='{pellet.title[:50]}...', score={pellet.score}, tags={len(pellet.tags)}"
            )

        return result

    except Exception as e:
        logger.error(f"Pellet summary generation failed: error={str(e)}")
        raise


if __name__ == "__main__":
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=global_settings.server_port,
            log_level="info",
            reload=False,
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Running in test mode...")
        # 在测试模式下，只打印信息
        print("AI Provider Service - Modular Version")
        print(f"Would listen on port: {global_settings.server_port}")
