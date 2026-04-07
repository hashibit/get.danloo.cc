"""
AI Provider API models - shared between services
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from common.api_models.material_model import MaterialContentData


class BaseRequest(BaseModel):
    pass


class Tag(BaseModel):
    """Tag model from AI Provider."""

    tag: str = Field(alias="tag")
    score: int = Field(alias="score", default=0)


class KnowledgeCategory(BaseModel):
    """Knowledge classification category."""

    category1: str = Field(description="Top-level knowledge domain")
    category2: str = Field(description="Specific knowledge area")
    category3: List[str] = Field(description="Detailed knowledge topics")
    confidence: int = Field(description="Confidence score 0-100")


class KnowledgePoint(BaseModel):
    """Individual knowledge point extracted from content."""

    title: str = Field(description="Clear, concise title of the knowledge point")
    description: str = Field(
        description="Brief explanation of what this knowledge point covers"
    )
    category: KnowledgeCategory = Field(
        description="Classification using the provided hierarchy"
    )
    tags: List[Tag] = Field(
        default_factory=list, description="Array of relevant tags with scores"
    )
    analysis_approach: str = Field(
        description="Brief description of how this knowledge point was identified"
    )


class ClassificationResult(BaseModel):
    knowledge_points: List[KnowledgePoint] = Field(
        default_factory=list, description="1-3 most significant knowledge points"
    )
    language: str = Field(default="", description="Primary language of the content")
    llm_result: Dict[str, Any] = Field(default_factory=dict)


class SuggestedTag(BaseModel):
    """建议的标签"""

    name: str
    color: Optional[str] = None
    description: Optional[str] = None
    weight: float = 1.0


class PelletSummary(BaseModel):
    """Pellet摘要 - 用于第一阶段生成主题列表"""

    title: str = Field(description="主题标题")
    abstract: str = Field(description="主题主旨摘要，100-200字")


class PelletPage(BaseModel):
    """Pellet完整页面 - 第二阶段生成的详细文章"""

    title: str = Field(description="文章标题")
    content: str = Field(description="文章完整内容")
    score: float = Field(default=75.0, description="内容质量评分 0-100")
    tags: List[SuggestedTag] = Field(default_factory=list, description="推荐标签列表")


class ExtractContentRequest(BaseModel):
    """Content extraction request to AI Provider - shared between services."""

    content_id: str
    text_content: Optional[str] = None
    http_video_url: Optional[str] = None
    http_image_urls: Optional[List[str]] = None
    object_content_base64: Optional[str] = None
    object_content_type: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None


class SummaryPelletRequest(BaseModel):
    """Pellet summary generation request."""

    results: List[ClassificationResult] = Field(description="分类结果列表")
    params: List[MaterialContentData] = Field(description="素材内容列表")


class ClassifyMaterialRequest(BaseModel):
    """AI Proxy classify material request."""

    object_bucket: str = Field(description="S3 bucket name containing the object")
    object_key: str = Field(description="S3 object key")


class ClassifyMaterialResponse(BaseModel):
    """AI Proxy classify material response."""

    result_bucket: str = Field(
        description="S3 bucket name containing the classification result"
    )
    result_key: str = Field(description="S3 object key for the classification result")
