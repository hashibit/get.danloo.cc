"""Main LLM caller service."""

import logging
import random
from typing import Any
from functools import wraps

from fastapi import HTTPException
from api_models.material_model import MaterialContentData
from retrying import retry

from ..config import global_settings

from common.api_models.ai_provider import (
    ClassificationResult,
    PelletSummary,
    PelletPage,
    SuggestedTag,
)

from ..utils.helpers import (
    LanguageMap,
    must_deserialize_json_to_class,
    must_deserialize_json_to_list,
    must_parse_xml_response,
    must_parse_pellet_summaries_xml,
)

from ..prompts import prompt_factory
from .utils.video_processor import VideoProcessor
from .utils.image_processor import ImageProcessor
from .llm_clients import (
    get_anthropic_client,
    get_openai_completion,
    get_bedrock_cluster,
)
from .exceptions import BedrockCallException


logger = logging.getLogger(__name__)


def configurable_retry(func):
    """可配置的重试装饰器"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        retry_decorator = retry(
            stop_max_attempt_number=self.retry_max_attempts,
            wait_exponential_multiplier=self.retry_wait_multiplier,
        )
        return retry_decorator(func)(self, *args, **kwargs)

    return wrapper


class LLMCaller:
    """LLM调用服务"""

    def __init__(self):
        # 流量分配配置
        self.anthropic_traffic_ratio = global_settings.anthropic.traffic_ratio
        self.openai_traffic_ratio = global_settings.openai.traffic_ratio

        # 重试配置
        self.retry_max_attempts = global_settings.retry_max_attempts
        self.retry_wait_multiplier = global_settings.retry_wait_multiplier

        # 初始化视频处理器
        self.video_processor = VideoProcessor()
        self.image_processor = ImageProcessor()

    @configurable_retry
    def extract_content(
        self,
        content_id: int,
        text_content: str | None = None,
        http_video_url: str | None = None,
        http_image_urls: list[str] | None = None,
        object_content_base64: str | None = None,
        object_content_type: str | None = None,
        extras: dict[str, Any] | None = None,
    ) -> ClassificationResult:
        """统一的内容提取方法，支持文本和视频"""
        logger.info(f"Content ID: {content_id} 调用 LLM 进行统一内容提取")

        # 准备提取请求的参数
        image_frames_b64 = []
        video_data_b64 = None

        # 处理对象内容（base64编码的内容）
        if object_content_base64 and object_content_type:
            logger.info(f"Content ID: {content_id} 使用对象内容分析")
            if object_content_type.startswith("video/"):
                video_data_b64 = object_content_base64
            elif object_content_type.startswith("image/"):
                image_frames_b64 = [object_content_base64]
            elif object_content_type.startswith("text/") or object_content_type in [
                "application/json",
                "application/xml",
            ]:
                text_content = object_content_base64
            else:
                raise ValueError(
                    f"Unsupported content type: {object_content_type}. Expected video/*, image/*, text/*, application/json, or application/xml"
                )

        # 处理HTTP视频URL
        elif http_video_url:
            logger.info(f"Content ID: {content_id} 使用视频URL分析")
            video_data_b64 = self.video_processor.video_url_to_base64(
                content_id, http_video_url
            )

        # 处理文本内容
        elif text_content:
            logger.info(f"Content ID: {content_id} 使用文本内容分析")

        # 如果没有提供任何内容，抛出异常
        else:
            raise ValueError(
                "至少需要提供一个内容参数（text_content, http_video_url, http_image_urls, object_content_base64）"
            )

        # 处理HTTP图片URL列表
        if http_image_urls:
            logger.info(f"Content ID: {content_id} 添加额外的图片素材分析")
            for img_url in http_image_urls:
                img_b64 = self.image_processor.url_to_base64(img_url)
                image_frames_b64.append(img_b64)

        # 添加语言 prompt（默认语言检测）
        content_language = (
            "According to the understanding of the content, "
            "detect the most possible language code of the content, "
            "(note that only output language code, not language name.）, "
            "If traditional Chinese is recognized, traditional Chinese must be output. "
        )
        tags_language = "You should detect language of the content first, then output tags in the same language."

        # 构建prompt
        prompt = (
            prompt_factory.get_prompt_for_unified_content_classification()
            .replace("{{ all-categories }}", prompt_factory.all_categories_clean)
            .replace("{{ tags-language-description }}", tags_language)
            .replace("{{ content-language-description }}", content_language)
        )

        # 调用_do_extract_content方法处理内容
        result = self._do_extract_content(
            content_id,
            prompt,
            text_content,
            video_data_b64,
            image_frames_b64,
        )

        logger.info(
            f"Content ID: {content_id} 成功通过 LLM 获取到 categories 和 tags，语言： {result.language}"
        )
        return result

    def _do_extract_content(
        self,
        content_id: int,
        prompt: str,
        text_content: str | None,
        video_data_b64: str | None,
        image_frames_b64: list[str],
    ) -> ClassificationResult:
        # 根据内容类型选择合适的处理方式
        if video_data_b64 or image_frames_b64:
            # 视频内容处理
            logger.info(f"Content ID: {content_id} 处理视频内容")
            response_text = get_bedrock_cluster().analyze_video(
                content_id,
                prompt,
                video_data_b64=video_data_b64,
                image_frames_b64=image_frames_b64,
            )
        else:
            # 纯文本内容处理
            logger.info(f"Content ID: {content_id} 处理文本内容")
            assert text_content is not None
            response_text = self._gpt_traffic_route(content_id, prompt, text_content)
        logger.debug(f"Content ID: {content_id} 调用 LLM 获取提取结果: {response_text}")

        # 解析结果
        result = must_deserialize_json_to_class(
            content_id, response_text, ClassificationResult
        )

        return result

    @configurable_retry
    def summary_pellet(
        self,
        content_id: int,
        results: list[ClassificationResult],
        params: list[MaterialContentData],
    ) -> list[PelletPage]:
        """
        两阶段生成Pellet:
        阶段1: 生成1-3个pellet summaries(主题摘要列表)
        阶段2: 对每个summary生成详细的pellet page(完整文章)

        Args:
            content_id: 内容ID
            results: 材料处理结果列表
            params: 材料内容列表

        Returns:
            List[PelletPage]: Pellet完整页面列表
        """
        try:
            content_id = 0

            # 合并所有处理结果的内容
            combined_result_text = self._combine_results_text(results)

            logger.info(
                f"Content ID: {content_id} 开始两阶段Pellet生成，包含{len(results)}个材料结果"
            )

            # ========== 阶段1: 生成 pellet summaries (主题摘要列表) ==========
            pellet_summaries = self._generate_pellet_summaries(content_id, combined_result_text)
            logger.info(
                f"Content ID: {content_id} 阶段1完成，生成了{len(pellet_summaries)}个主题摘要："
            )
            for i, summary in enumerate(pellet_summaries, 1):
                logger.info(
                    f"  主题{i}: {summary['title']}"
                )
                logger.info(
                    f"  摘要{i}: {summary['abstract'][:100]}..." if len(summary['abstract']) > 100 else f"  摘要{i}: {summary['abstract']}"
                )

            # ========== 阶段2: 对每个 summary 生成详细的 pellet page ==========
            pellet_pages = []
            for i, summary in enumerate(pellet_summaries, 1):
                logger.info(
                    f"Content ID: {content_id} 阶段2 - 生成第{i}/{len(pellet_summaries)}篇文章: {summary['title']}"
                )
                try:
                    page = self._generate_pellet_page_for_summary(
                        content_id, summary, combined_result_text
                    )
                    pellet_pages.append(page)
                except Exception as e:
                    logger.error(
                        f"Content ID: {content_id} 生成第{i}篇文章失败: {str(e)}，继续处理下一篇"
                    )
                    continue

            if not pellet_pages:
                raise ValueError("所有文章生成都失败了")

            logger.info(
                f"Content ID: {content_id} Pellet生成完成，共生成{len(pellet_pages)}篇完整文章"
            )
            return pellet_pages

        except Exception as e:
            logger.error(f"Content ID: {content_id} Pellet生成失败: {str(e)}")
            raise

    def _generate_pellet_summaries(
        self, content_id: int, combined_result_text: str
    ) -> list[dict]:
        """阶段1: 生成pellet summaries (主题摘要列表)

        Args:
            content_id: 内容ID
            combined_result_text: 合并后的知识点文本

        Returns:
            list[dict]: [{"title": "...", "abstract": "..."}]
        """
        # 构建阶段1提示词
        prompt = prompt_factory.get_prompt_for_pellet_summaries()

        message = [
            "=====================  所有的知识点  ===================",
            combined_result_text,
        ]

        logger.info(f"Content ID: {content_id} 阶段1: 生成pellet summaries")

        # 调用LLM生成主题摘要列表，限制2048 tokens足够
        llm_response = self._gpt_traffic_route(
            content_id, prompt, "\n".join(message), max_tokens=2048
        )

        # 解析XML响应
        pellet_summaries = must_parse_pellet_summaries_xml(content_id, llm_response)

        return pellet_summaries

    def _generate_pellet_page_for_summary(
        self, content_id: int, summary: dict, combined_result_text: str
    ) -> PelletPage:
        """阶段2: 为单个summary生成详细的pellet page

        Args:
            content_id: 内容ID
            summary: {"title": "...", "abstract": "..."}
            combined_result_text: 合并后的知识点文本

        Returns:
            PelletPage: 详细的完整文章
        """
        # 构建阶段2提示词
        prompt = prompt_factory.get_prompt_for_pellet_page()

        # 添加主题指导
        message = [
            f"=====================  文章主题  ===================",
            f"标题: {summary['title']}",
            f"主旨: {summary['abstract']}",
            "",
            "=====================  相关知识点  ===================",
            combined_result_text,
        ]

        logger.info(
            f"Content ID: {content_id} 阶段2: 生成完整文章 - {summary['title']}"
        )

        # 调用LLM生成详细文章
        llm_response = self._gpt_traffic_route(
            content_id, prompt, "\n".join(message), max_tokens=8192
        )

        # 解析XML响应(只有1篇文章)
        result_list = must_parse_xml_response(
            content_id, llm_response, PelletPage
        )

        if not result_list:
            raise ValueError(f"未能生成文章: {summary['title']}")

        return result_list[0]  # 返回第一篇(也是唯一一篇)

    def _combine_results_text(self, results: list[ClassificationResult]) -> str:
        """合并所有ClassificationResult的知识点内容"""
        combined_parts = []

        for i, classification_result in enumerate(results, 1):
            combined_parts.append(f"=== 材料 {i} 分析结果 ===")
            combined_parts.append(f"语言: {classification_result.language}")

            if classification_result.knowledge_points:
                combined_parts.append("知识点:")
                for j, knowledge_point in enumerate(
                    classification_result.knowledge_points, 1
                ):
                    combined_parts.append(f"{j}. **{knowledge_point.title}**")
                    combined_parts.append(f"   描述: {knowledge_point.description}")
                    # combined_parts.append(
                    #     f"   分类: {knowledge_point.category.category1} > {knowledge_point.category.category2} > {', '.join(knowledge_point.category.category3)}"
                    # )
                    # combined_parts.append(
                    #     f"   分析方法: {knowledge_point.analysis_approach}"
                    # )
                    # if knowledge_point.tags:
                    #     tag_names = [
                    #         f"{tag.tag}({tag.score})" for tag in knowledge_point.tags
                    #     ]
                    #     combined_parts.append(f"   标签: {', '.join(tag_names)}")
                    combined_parts.append("")
            # else:
            #     combined_parts.append("未识别到具体知识点")

            combined_parts.append("")  # 空行分隔

        return "\n".join(combined_parts)

    def _gpt_traffic_route(self, content_id: int, prompt: str, text: str, max_tokens: int = 4096) -> str:
        """GPT流量路由

        Args:
            content_id: 内容ID
            prompt: 提示词
            text: 输入文本
            max_tokens: 最大输出token数，默认4096
        """
        rand = random.randint(0, 99)
        # 当前仅仅走 openai 接口
        rand = 0
        if rand < self.anthropic_traffic_ratio * 100:
            logger.info(f"Content ID: {content_id} gpt traffic route to anthropic with max_tokens={max_tokens}")
            client = get_anthropic_client()
            if client:
                result = client.request_anthropic_completion(
                    content_id, prompt, text, max_tokens=max_tokens
                )
                return result["content"]
            else:
                logger.error(f"can not get get_anthropic_client")
                return ""
        elif rand < self.openai_traffic_ratio * 100:
            logger.info(f"Content ID: {content_id} gpt traffic route to openai with max_tokens={max_tokens}")
            return get_openai_completion().request_openai_chat_completion(
                content_id, prompt, text
            )
        else:
            logger.info(f"Content ID: {content_id} gpt traffic route to bedrock with max_tokens={max_tokens}")
            return get_bedrock_cluster().invoke_model(content_id, prompt, text)


# 全局实例
llm_caller = LLMCaller()
