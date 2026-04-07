"""Service for reading material data and content from backend database and object storage"""

import os
import base64
import tempfile
import json
from typing import Optional, Any, Dict, List
from dataclasses import dataclass

from database import get_database

from common.database_models.material_model import MaterialDB
from common.database_models.object_model import ObjectDB
from common.api_models.material_model import MaterialContentData
from common.api_models.ai_provider import KnowledgePoint, KnowledgeCategory
from object.services.object_service import ObjectService, ObjectServiceError


@dataclass
class TokenUsageMetadata:
    """Token usage metadata from AI processing"""
    model_id: str  # 修正为model_id以匹配TokenUsageDB
    duration_seconds: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: Optional[str] = None


@dataclass
class ClassificationResultData:
    """Structured classification result data"""
    knowledge_points: List[KnowledgePoint]
    language: str
    summary: str
    metadata: TokenUsageMetadata


def get_object_service() -> ObjectService:
    """Get ObjectService instance from environment variables."""
    try:
        return ObjectService.from_env()
    except ObjectServiceError as e:
        raise Exception("unable to get s3 object service from env.")


class MaterialContentService:
    # 支持的内容类型 - 标准化 MIME types
    SUPPORTED_CONTENT_TYPES = {
        # Text types
        "text/plain",
        "text/html",
        "text/css",
        "text/javascript",
        "application/json",
        "application/xml",
        # PDF
        "application/pdf",
        # Image types
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        # Video types
        "video/mp4",
        "video/mpeg",
        "video/quicktime",
        "video/x-msvideo",
        "video/webm",
        # Audio types
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/ogg",
        "audio/webm",
        "audio/aac",
    }

    def __init__(self):
        # Use ObjectService for S3 operations
        self.object_service = get_object_service()
        self.s3_client = self.object_service.s3_client
        self.s3_bucket = self.object_service.bucket

    def _is_supported_content_type(self, content_type: str) -> bool:
        """检查内容类型是否受支持"""
        return content_type in self.SUPPORTED_CONTENT_TYPES

    def get_material_info(self, material_id: str) -> Optional[MaterialDB]:
        """Get material information from backend database"""
        db = next(get_database())
        try:
            material = db.query(MaterialDB).filter(MaterialDB.id == material_id).first()
            return material
        finally:
            db.close()

    def get_object_info(self, object_id: str) -> Optional[ObjectDB]:
        """Get object information from backend database"""
        db = next(get_database())
        try:
            obj = db.query(ObjectDB).filter(ObjectDB.id == object_id).first()
            return obj
        finally:
            db.close()

    def read_content_from_s3(self, object_id: str, content_type: str) -> str:
        """Read file content from S3 using ObjectService - downloads to temporary file for processing

        Args:
            object_id: The object ID to read from S3
            content_type: The content type of the file
            return_base64: If True, always return content as base64 (default). If False, return text content as decoded string.
        """
        if not self._is_supported_content_type(content_type):
            supported_types = ", ".join(sorted(self.SUPPORTED_CONTENT_TYPES))
            raise Exception(
                f"Unsupported content type: {content_type}. Supported types: {supported_types}"
            )

        try:
            # Use ObjectService to download to temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name

            # Download file using ObjectService
            db = next(get_database())
            try:
                self.object_service.download_to_local(db, object_id, temp_path)
            finally:
                db.close()

            # Read the temporary file
            with open(temp_path, "rb") as f:
                raw_content = f.read()

            # Clean up temporary file
            os.unlink(temp_path)

            # Generate base64 for AI provider
            if content_type.startswith("text/") or content_type in [
                "application/json",
                "application/xml",
            ]:
                # Text content needs to be decoded first, then encoded to base64
                try:
                    text_content = raw_content.decode("utf-8")
                except UnicodeDecodeError:
                    text_content = raw_content.decode("latin-1")
                return base64.b64encode(text_content.encode("utf-8")).decode("utf-8")
            else:
                # Non-text content is directly converted to base64
                return base64.b64encode(raw_content).decode("utf-8")

        except Exception as e:
            print(f"Error reading from S3 object {object_id}: {str(e)}")
            raise

    def get_material_b64_content_by_id(self, material_id: str) -> MaterialContentData:
        """Get complete material information and content using object_id directly"""
        # If material_id is provided, get additional info from material
        material_title = f"Material {material_id}"
        material_content_type = "application/octet-stream"  # default
        material_file_size = None
        material_user_id = None

        material = self.get_material_info(material_id)
        if not material:
            raise Exception(f"material {material_id} not found in database")

        material_title = str(material.title)
        material_content_type = str(material.content_type)
        material_file_size = str(material.file_size)
        material_user_id = str(material.user_id)
        object_id = str(material.object_id)

        # Get object info using ObjectService
        obj = self.get_object_info(object_id)
        if not obj:
            raise Exception(
                f"Object {object_id} of material {material_id} not found in database"
            )

        # Get content as base64 for AI provider
        content_base64 = self.read_content_from_s3(object_id, material_content_type)

        return MaterialContentData(
            material_id=material_id,
            object_id=object_id,
            title=material_title,
            content_type=material_content_type,
            content_base64=content_base64,  # Base64 encoded content for AI provider
            file_size=material_file_size,
            user_id=material_user_id,
        )

    def read_classification_results_from_s3(self, bucket: str, key: str) -> ClassificationResultData:
        """Read classification results from S3 bucket and return structured data

        Args:
            bucket: S3 bucket name where the classification results are stored
            key: S3 object key for the classification results file

        Returns:
            ClassificationResultData: Structured classification result with parsed knowledge points and metadata
        """
        try:
            # Download the file directly from S3 using boto3
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()

            # Decode content and parse as JSON
            content_str = content.decode('utf-8')
            result_json = json.loads(content_str)

            # Parse knowledge points
            knowledge_points = []
            if "knowledge_points" in result_json:
                for kp_title in result_json["knowledge_points"]:
                    knowledge_points.append(
                        KnowledgePoint(
                            title=kp_title,
                            description=f"Knowledge point: {kp_title}",
                            category=KnowledgeCategory(
                                category1="General",
                                category2="Knowledge",
                                category3=["Learning"],
                                confidence=85
                            ),
                            tags=[],
                            analysis_approach="Extracted from AI classification result"
                        )
                    )

            # Parse metadata
            metadata_json = result_json.get("metadata", {})
            metadata = TokenUsageMetadata(
                model_id=metadata_json.get("model", "unknown"),  # 从"model"字段读取到model_id
                duration_seconds=metadata_json.get("duration_seconds", 0.0),
                prompt_tokens=metadata_json.get("prompt_tokens", 0),
                completion_tokens=metadata_json.get("completion_tokens", 0),
                total_tokens=metadata_json.get("total_tokens", 0),
                finish_reason=metadata_json.get("finish_reason")
            )

            # Create structured result
            return ClassificationResultData(
                knowledge_points=knowledge_points,
                language=result_json.get("language", "zh-CN"),
                summary=result_json.get("summary", "Classification completed"),
                metadata=metadata
            )

        except Exception as e:
            print(f"Error reading classification results from S3 bucket {bucket}, key {key}: {str(e)}")
            raise Exception(f"Failed to read classification results from S3: {str(e)}")

    def read_file_from_s3(self, bucket: str, key: str) -> str:
        """Read file content from S3 bucket and return as string

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            str: File content as string
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            return content.decode('utf-8')
        except Exception as e:
            print(f"Error reading file from S3 bucket {bucket}, key {key}: {str(e)}")
            raise Exception(f"Failed to read file from S3: {str(e)}")

    def write_file_to_s3(self, bucket: str, key: str, content: str) -> bool:
        """Write file content to S3 bucket

        Args:
            bucket: S3 bucket name
            key: S3 object key
            content: File content as string

        Returns:
            bool: True if successful
        """
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            print(f"Error writing file to S3 bucket {bucket}, key {key}: {str(e)}")
            raise Exception(f"Failed to write file to S3: {str(e)}")


material_content_service = MaterialContentService()
