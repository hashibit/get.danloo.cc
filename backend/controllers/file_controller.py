"""File upload controller for handling presigned URL workflow."""

# from typing import Optional  # unused
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_database
from common.api_models.object_model import ObjectCreate, ObjectResponse, FileInfo
from common.object.services.object_service import (
    ObjectService,
    ObjectServiceError,
    ObjectNotFoundError,
)
from common.object.services.buckets import BUCKET_UPLOADS

from backend.middleware.auth import get_current_user

router = APIRouter()


class FileUploadRequest(BaseModel):
    """Request model for file upload initiation."""

    filename: str
    file_size: int | None = None
    content_type: str | None = None


class FileUploadResponse(BaseModel):
    """Response model for file upload initiation."""

    object_id: str
    presigned_url: str
    expires_in: int = 3600


class FileCommitRequest(BaseModel):
    """Request model for file upload commit."""

    object_id: str
    file_info: FileInfo | None = None


def get_object_service() -> ObjectService:
    """Get ObjectService instance from environment variables."""
    try:
        return ObjectService.from_env(BUCKET_UPLOADS)
    except ObjectServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Object service initialization failed: {str(e)}",
        )


@router.post("/upload/init", response_model=FileUploadResponse)
async def init_file_upload(
    request: FileUploadRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    object_service: ObjectService = Depends(get_object_service),
):
    """
    Initialize file upload process.

    Creates object record and generates presigned URL for direct S3 upload.
    """
    try:
        # Prepare file info
        file_info = FileInfo()
        if request.file_size:
            file_info.size = request.file_size
        if request.content_type:
            file_info.type = request.content_type

        # Add user info
        file_info.uploaded_by = current_user.get("user_id", current_user.get("id"))

        # Create object record
        object_data = ObjectCreate(name=request.filename, file_info=file_info)

        obj_db = object_service.create_object(db, object_data)

        # Generate presigned URL with Content-Type for signature consistency
        presigned_url = object_service.generate_presigned_upload_url_for_object(
            db, obj_db.id, content_type=request.content_type
        )

        return FileUploadResponse(
            object_id=obj_db.id, presigned_url=presigned_url, expires_in=3600
        )

    except ObjectServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.post("/upload/commit", response_model=ObjectResponse)
async def commit_file_upload(
    request: FileCommitRequest,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    object_service: ObjectService = Depends(get_object_service),
):
    """
    Commit file upload after successful S3 upload.

    Marks the object as uploaded and updates file information.
    """
    try:
        # Verify object exists and belongs to current user
        db_object = object_service.get_object(db, request.object_id)
        if not db_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
            )

        # Check if user has permission (object was created by this user)
        if db_object.file_info:
            if db_object.file_info.get("uploaded_by") != current_user.get(
                "user_id", current_user.get("id")
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
                )

        # Mark as uploaded
        updated_object = object_service.mark_uploaded(
            db, request.object_id, request.file_info
        )

        return ObjectResponse.model_validate(updated_object)

    except ObjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
        )
    except ObjectServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get("/objects/{object_id}", response_model=ObjectResponse)
async def get_file_object(
    object_id: str,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    object_service: ObjectService = Depends(get_object_service),
):
    """Get file object information."""
    try:
        db_object = object_service.get_object(db, object_id)
        if not db_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
            )

        # Check permission
        if db_object.file_info and db_object.file_info.get(
            "uploaded_by"
        ) != current_user.get("user_id", current_user.get("id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        return ObjectResponse.from_orm(db_object)

    except ObjectServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/objects/{object_id}")
async def delete_file_object(
    object_id: str,
    db: Session = Depends(get_database),
    current_user: dict = Depends(get_current_user),
    object_service: ObjectService = Depends(get_object_service),
):
    """Delete file object and associated S3 file."""
    try:
        db_object = object_service.get_object(db, object_id)
        if not db_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
            )

        # Check permission
        if db_object.file_info and db_object.file_info.get(
            "uploaded_by"
        ) != current_user.get("user_id", current_user.get("id")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

        # Delete object
        object_service.delete_object(db, object_id, delete_from_s3=True)

        return {"message": "Object deleted successfully"}

    except ObjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
        )
    except ObjectServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
