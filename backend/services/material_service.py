import os
import httpx
from datetime import date
from sqlalchemy.orm import Session
from common.database_models.material_model import MaterialDB
from common.utils.ulid_utils import generate_ulid
import tempfile
# import json  # unused
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from common.api_models.material_model import (
    MaterialFromObjectCreate,
)
from common.api_models.object_model import FileInfo

from common.object.services.buckets import BUCKET_UPLOADS, format_upload_object_key


class MaterialService:
    def __init__(self):
        self.upload_dir = "uploads"

        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def get_material_by_id(self, db: Session, material_id: str) -> MaterialDB | None:
        """Get material by ID from database"""
        return db.query(MaterialDB).filter(MaterialDB.id == material_id).first()

    def get_materials_by_user(
        self, db: Session, user_id: str, limit: int | None = 10
    ) -> list[MaterialDB]:
        """Get materials by user ID from database"""
        query = db.query(MaterialDB).filter(MaterialDB.user_id == user_id)
        query = query.order_by(MaterialDB.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def create_material_from_object(
        self, db: Session, user_id: str, data: MaterialFromObjectCreate
    ) -> MaterialDB:
        """Create a new material from uploaded file object"""
        # Get file object info
        from common.database_models.object_model import ObjectDB

        file_obj = db.query(ObjectDB).filter(ObjectDB.id == data.file_object_id).first()
        if not file_obj:
            raise ValueError("File object not found")

        # Verify user owns the file object
        if file_obj.file_info and file_obj.file_info.get("uploaded_by") != user_id:
            raise ValueError("Access denied to file object")

        material_id = generate_ulid()

        # Create material record using file object info
        new_material = MaterialDB(
            id=material_id,
            user_id=user_id,
            title=data.title,
            content_type=data.content_type,
            object_id=data.file_object_id,
            file_path=file_obj.s3_path,
            file_size=file_obj.file_info.get("size", 0) if file_obj.file_info else 0,
        )

        db.add(new_material)
        db.commit()
        db.refresh(new_material)
        return new_material

    async def create_material_from_url(
        self, db: Session, user_id: str, data
    ) -> MaterialDB:
        """Create material by fetching content from URL"""
        try:
            # Validate URL
            parsed_url = urlparse(data.url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")

            # Fetch content from URL using httpx
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(data.url, headers=headers)
                response.raise_for_status()

            # Extract text content
            content_type = response.headers.get("content-type", "").lower()
            if "html" in content_type:
                soup = BeautifulSoup(response.content, "html.parser")
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text_content = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in text_content.splitlines())
                text_content = "\n".join(line for line in lines if line)
            else:
                text_content = response.text

            # Create file object in MinIO with the fetched content
            file_content = text_content.encode("utf-8")
            file_object = await self._create_file_object_from_content(
                file_content,
                f"{data.title}.txt",
                user_id,
                {
                    "source_url": data.url,
                    "content_type": content_type,
                    "input_type": "url",
                },
            )

            # Create material record
            material_id = generate_ulid()
            new_material = MaterialDB(
                id=material_id,
                user_id=user_id,
                title=data.title,
                content_type=data.content_type,
                file_path=f"object:{file_object.id}",
                file_size=len(file_content),
            )

            db.add(new_material)
            db.commit()
            db.refresh(new_material)
            return new_material

        except httpx.RequestError as e:
            raise ValueError(f"Failed to fetch content from URL: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing URL: {str(e)}")

    async def create_material_from_text(
        self, db: Session, user_id: str, data
    ) -> MaterialDB:
        """Create material from text content"""
        try:
            # Create file object in MinIO with the text content
            file_content = data.text_content.encode("utf-8")
            file_object = await self._create_file_object_from_content(
                file_content, f"{data.title}.txt", user_id, {"input_type": "text_paste"}
            )

            # Create material record
            material_id = generate_ulid()
            new_material = MaterialDB(
                id=material_id,
                user_id=user_id,
                title=data.title,
                content_type=data.content_type,
                file_path=f"object:{file_object.id}",
                file_size=len(file_content),
            )

            db.add(new_material)
            db.commit()
            db.refresh(new_material)
            return new_material

        except Exception as e:
            raise ValueError(f"Error processing text content: {str(e)}")

    async def _create_file_object_from_content(
        self, content: bytes, filename: str, user_id: str, metadata: dict | None = None
    ):
        """Helper method to create file object in MinIO from content"""
        from common.database_models.object_model import ObjectDB
        from common.object.services.object_service import ObjectService
        from database import get_database

        # Get object service instance
        object_service = ObjectService.from_env(BUCKET_UPLOADS)
        object_id = generate_ulid()

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

            object_key = format_upload_object_key(
                user_id, date.today().isoformat(), object_id, filename
            )

            # Upload file to MinIO
            object_service.upload_file(BUCKET_UPLOADS, object_key, temp_file_path)

        # Create file info
        file_info = FileInfo(
            filename=filename,
            size=len(content),
            uploaded_by=user_id,
            content_type="text/plain",
        )

        # Merge metadata into file_info
        if metadata:
            for key, value in metadata.items():
                if hasattr(file_info, key):
                    setattr(file_info, key, value)
                # For attributes not in FileInfo, we'll store them in additional_metadata
                else:
                    if file_info.additional_metadata is None:
                        file_info.additional_metadata = {}
                    file_info.additional_metadata[key] = value

        # Get database session
        db_gen = get_database()
        db = next(db_gen)

        try:
            # Create object record in database
            object_record = ObjectDB(
                id=object_id,
                name=filename,
                s3_path=f"{BUCKET_UPLOADS}/{object_key}",
                file_info=file_info.model_dump(),
                is_uploaded=True,
            )

            db.add(object_record)
            db.commit()
            db.refresh(object_record)

            return object_record
        finally:
            db.close()


material_service = MaterialService()
