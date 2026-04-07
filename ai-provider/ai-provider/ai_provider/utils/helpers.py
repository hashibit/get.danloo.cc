"""Helper utilities for LLM Proxy."""

import json
import re
import yaml
import xml.etree.ElementTree as ET
from typing import TypeVar, Type, List
import logging

from ai_provider.prompts.language_factory import language_factory
from api_models.ai_provider import PelletPage

from .json_parser import JsonParser

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LanguageMap:
    @staticmethod
    def get_language_code(language_name: str) -> str:
        """根据语言名称获取语言编码"""
        return language_factory.all_language_names.get(language_name, "")

    @staticmethod
    def get_language_name(language_code: str) -> str:
        """根据语言编码获取语言名称"""
        return language_factory.all_language_codes.get(language_code, "")


class SourceDataContentUtils:
    """源数据内容工具"""

    @staticmethod
    def get_video_url_from_s3_uri(s3_uri: str) -> str:
        """从S3 URI获取视频URL"""
        if not s3_uri.startswith("s3://"):
            return s3_uri

        # 简单的S3 URI到URL的转换
        bucket_and_key = s3_uri[5:]  # 去掉 s3://
        parts = bucket_and_key.split("/", 1)
        if len(parts) == 2:
            bucket, key = parts
            return f"https://{bucket}.s3.amazonaws.com/{key}"

        return s3_uri

    @staticmethod
    def extract_image_urls_from_content(content: str) -> list[str]:
        """从内容中提取图片URL"""
        if not content:
            return []

        # 使用正则表达式匹配图片URL
        image_url_pattern = r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|bmp|webp)'
        image_urls = re.findall(image_url_pattern, content, re.IGNORECASE)

        return image_urls


def must_deserialize_json_to_class(
    content_id: int, input_string: str, target_class: Type[T]
) -> T:
    """必须反序列化JSON到指定类，如果失败则抛出异常"""
    json_string = JsonParser.try_find_json_object_string(input_string)
    if json_string:
        json_string = JsonParser.fix_wrong_escapes(json_string)

    if not json_string:
        raise ValueError(
            f"{content_id} mustDeserializeJSONToClass 输入无法找到有效JSON[{input_string}]，无法反序列化"
        )

    result = JsonParser.try_deserialize(json_string, target_class)
    if result is not None:
        return result

    raise ValueError(
        f"修复后还不是合法的 JSON：{json_string}，无法序列化到：{target_class}"
    )


def must_deserialize_json_to_list(
    content_id: int, input_string: str, target_class: Type[T]
) -> list[T]:
    """必须反序列化JSON到指定类的列表，如果失败则抛出异常"""
    json_string = JsonParser.try_find_json_array_string(input_string)
    if json_string:
        json_string = JsonParser.fix_wrong_escapes(json_string)

    if not json_string:
        raise ValueError(
            f"{content_id} mustDeserializeJSONToList 输入无法找到有效JSON[{input_string}]，无法反序列化"
        )

    try:
        data = json.loads(json_string)
        if not isinstance(data, list):
            raise ValueError(f"Expected list but got {type(data)}")

        result = []
        for item in data:
            if hasattr(target_class, "parse_obj"):
                result.append(target_class.parse_obj(item))
            elif hasattr(target_class, "model_validate"):
                result.append(target_class.model_validate(item))
            else:
                result.append(target_class(**item))

        return result
    except Exception as e:
        raise ValueError(
            f"修复后还不是合法的 JSON：{json_string}，无法序列化到：{target_class}"
        )


def must_parse_yaml_response(
    content_id: int, llm_response: str, target_class: Type[T]
) -> List[T]:
    """解析LLM的YAML响应并转换为指定类型的列表"""
    try:
        # 尝试找到YAML内容 (在```yaml 和 ``` 之间)
        yaml_start = llm_response.find("```yaml")
        if yaml_start == -1:
            yaml_start = llm_response.find("```yml")
        if yaml_start == -1:
            # 如果没有代码块标记，尝试解析整个响应
            yaml_content = llm_response.strip()
        else:
            yaml_start += (
                7 if "```yaml" in llm_response[yaml_start : yaml_start + 7] else 6
            )
            yaml_end = llm_response.find("```", yaml_start)
            if yaml_end == -1:
                yaml_content = llm_response[yaml_start:].strip()
            else:
                yaml_content = llm_response[yaml_start:yaml_end].strip()

        # 解析YAML
        data = yaml.safe_load(yaml_content)

        if not isinstance(data, list):
            raise ValueError(f"Expected list but got {type(data)}")

        # 转换为目标类型
        result = []
        for i, item in enumerate(data):
            try:
                # 预处理：标准化字段名
                normalized_item = item

                if hasattr(target_class, "model_validate"):
                    # Pydantic v2
                    result.append(target_class.model_validate(normalized_item))
                elif hasattr(target_class, "parse_obj"):
                    # Pydantic v1
                    result.append(target_class.parse_obj(normalized_item))
                else:
                    # 普通类
                    result.append(target_class(**normalized_item))
            except Exception as e:
                logger.warning(
                    f"Content ID: {content_id} 跳过无效的YAML项目 {i}: {str(e)}"
                )
                logger.debug(f"无效项目内容: {item}")
                # 继续处理其他项目，不中断整个解析过程

        if not result:
            raise ValueError("所有YAML项目解析都失败了，没有有效的结果")

        logger.info(
            f"Content ID: {content_id} YAML解析成功，解析了{len(result)}个有效对象"
        )
        return result

    except yaml.YAMLError as e:
        logger.error(f"Content ID: {content_id} YAML解析失败: {str(e)}")
        logger.debug(f"原始响应: {llm_response}")
        raise ValueError(f"YAML解析失败: {str(e)}")
    except Exception as e:
        logger.error(f"Content ID: {content_id} 响应处理失败: {str(e)}")
        logger.debug(f"原始响应: {llm_response}")
        raise ValueError(f"响应处理失败: {str(e)}")


def must_parse_xml_response(
    content_id: int, llm_response: str, target_class: Type[PelletPage]
) -> list[PelletPage]:
    """解析LLM的XML响应并转换为指定类型的列表"""
    try:
        # 提取XML内容
        xml_content = _extract_xml_content(llm_response)

        # 解析XML
        root = ET.fromstring(xml_content)

        # 单篇文章格式: 直接就是 <article> 根标签
        if root.tag != "article":
            raise ValueError(
                f"Expected root tag 'article' but got '{root.tag}'"
            )

        # 转换为目标类型 - 只有一篇文章
        result = []
        try:
            # 提取数据 (root 本身就是 article 元素)
            item_data = _extract_article_data(root)
            result.append(target_class.model_validate(item_data))
        except Exception as e:
            logger.error(
                f"Content ID: {content_id} 解析文章失败: {str(e)}"
            )
            raise ValueError(f"解析文章失败: {str(e)}")

        logger.info(
            f"Content ID: {content_id} XML解析成功，解析了{len(result)}个有效对象"
        )
        return result

    except ET.ParseError as e:
        logger.error(f"Content ID: {content_id} XML解析失败: {str(e)}")
        logger.error(f"LLM原始响应(长度: {len(llm_response)} 字符):\n{llm_response}")
        raise ValueError(f"XML解析失败: {str(e)}")
    except Exception as e:
        logger.error(f"Content ID: {content_id} 响应处理失败: {str(e)}")
        logger.error(f"LLM原始响应(长度: {len(llm_response)} 字符):\n{llm_response}")
        raise ValueError(f"响应处理失败: {str(e)}")


def _extract_xml_content(llm_response: str) -> str:
    """从LLM响应中提取XML内容"""
    # 匹配 <article> 标签
    pattern = r"(<article>.*?</article>)"
    match = re.search(pattern, llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()

    # 如果没找到，尝试解析整个响应
    return llm_response.strip()


def _extract_article_data(article_elem: ET.Element) -> dict:
    """从XML元素提取文章数据"""
    data = {}

    # 提取标题
    title_elem = article_elem.find("title")
    data["title"] = title_elem.text if title_elem is not None else ""

    # 提取内容 (支持CDATA)
    content_elem = article_elem.find("text")
    data["content"] = content_elem.text if content_elem is not None else ""

    # 提取评分
    score_elem = article_elem.find("score")
    if score_elem and score_elem.text:
        data["score"] = float(score_elem.text)

    # 提取标签
    tags = []
    tags_elem = article_elem.find("tags")
    if tags_elem is not None:
        for tag_elem in tags_elem.findall("tag"):
            name_elem = tag_elem.find("name")
            weight_elem = tag_elem.find("weight")
            if name_elem and name_elem.text and weight_elem and weight_elem.text:
                tags.append({"name": name_elem.text, "weight": float(weight_elem.text)})

    data["tags"] = tags
    return data


def must_parse_pellet_summaries_xml(
    content_id: int, llm_response: str
) -> list:
    """解析LLM的Pellet Summaries XML响应并转换为PelletSummary列表

    Args:
        content_id: 内容ID
        llm_response: LLM响应内容

    Returns:
        list[dict]: PelletSummary数据列表 [{"title": "...", "abstract": "..."}]
    """
    try:
        # 提取XML内容
        pattern = r"(<summaries>.*?</summaries>)"
        match = re.search(pattern, llm_response, re.DOTALL)
        if match:
            xml_content = match.group(1).strip()
        else:
            xml_content = llm_response.strip()

        # 解析XML
        root = ET.fromstring(xml_content)

        if root.tag != "summaries":
            raise ValueError(
                f"Expected root tag 'summaries' but got '{root.tag}'"
            )

        # 转换为目标类型
        result = []
        for i, summary_elem in enumerate(root.findall("summary")):
            try:
                # 提取标题
                title_elem = summary_elem.find("title")
                title = title_elem.text if title_elem is not None else ""

                # 提取主旨
                abstract_elem = summary_elem.find("abstract")
                abstract = abstract_elem.text if abstract_elem is not None else ""

                if title and abstract:
                    result.append({
                        "title": title,
                        "abstract": abstract
                    })
                else:
                    logger.warning(
                        f"Content ID: {content_id} 跳过空的pellet summary {i}"
                    )

            except Exception as e:
                logger.warning(
                    f"Content ID: {content_id} 跳过无效的pellet summary {i}: {str(e)}"
                )

        if not result:
            raise ValueError("没有解析到有效的pellet summary")

        logger.info(
            f"Content ID: {content_id} Pellet summaries解析成功，解析了{len(result)}个主题摘要"
        )
        return result

    except ET.ParseError as e:
        logger.error(f"Content ID: {content_id} Pellet summaries XML解析失败: {str(e)}")
        logger.error(f"LLM原始响应(长度: {len(llm_response)} 字符):\n{llm_response}")
        raise ValueError(f"Pellet summaries XML解析失败: {str(e)}")
    except Exception as e:
        logger.error(f"Content ID: {content_id} Pellet summaries响应处理失败: {str(e)}")
        logger.error(f"LLM原始响应(长度: {len(llm_response)} 字符):\n{llm_response}")
        raise ValueError(f"Pellet summaries响应处理失败: {str(e)}")
