"""Object service for S3-based file management."""

import os
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from common.database_models.object_model import ObjectDB
from common.api_models.object_model import ObjectCreate, FileInfo
from common.object.services.buckets import format_upload_object_key
from common.utils.ulid_utils import generate_ulid


class ObjectServiceError(Exception):
    """Base exception for object service errors."""

    pass


class S3ConnectionError(ObjectServiceError):
    """Exception for S3 connection issues."""

    pass


class ObjectNotFoundError(ObjectServiceError):
    """Exception for object not found."""

    pass


class ObjectService:
    """Service for managing file objects with S3 integration."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
        external_endpoint: Optional[str] = None,
    ):
        """
        Initialize the object service.

        Args:
            endpoint: S3 endpoint URL (for internal service-to-service communication)
            access_key: S3 access key
            secret_key: S3 secret key
            bucket: S3 bucket name
            region: S3 region (default: us-east-1)
            s3_external_endpoint: External S3 endpoint URL (for frontend/client access)
        """
        self.bucket = bucket
        self.region = region
        self.endpoint = endpoint
        self.external_endpoint = external_endpoint
        self.access_key = access_key
        self.secret_key = secret_key

        # print(f"self.bucket: {self.bucket}")
        # print(f"self.region: {self.region}")
        # print(f"self.endpoint: {self.endpoint}")
        # print(f"self.external_endpoint: {self.external_endpoint}")
        # print(f"self.access_key: {self.access_key}")
        # print(f"self.secret_key: {self.secret_key}")

        try:
            # 使用 s3v4 签名（阿里云 OSS 等 S3 兼容服务需要）
            s3_config = Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            )

            self.s3_client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=s3_config,
            )

            # Test connection
            self.s3_client.head_bucket(Bucket=bucket)

        except NoCredentialsError as e:
            raise S3ConnectionError(f"Invalid S3 credentials: {e}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise S3ConnectionError(f"Bucket '{bucket}' not found")
            raise S3ConnectionError(f"S3 connection failed: {e}")
        except Exception as e:
            raise S3ConnectionError(f"Failed to initialize S3 client: {e}")

    def create_object(self, db: Session, object_data: ObjectCreate) -> ObjectDB:
        """
        Create a new object record.

        Args:
            db: Database session
            object_data: Object creation data

        Returns:
            Created object

        Raises:
            ObjectServiceError: If creation fails
        """
        try:
            # Generate unique S3 path
            object_id = generate_ulid()
            file_name = object_data.name

            file_info = object_data.file_info
            if not file_info or not file_info.uploaded_by:
                raise ObjectServiceError("File info and uploaded_by are required")

            user_id = file_info.uploaded_by
            object_key = format_upload_object_key(
                user_id, datetime.now().isoformat(), object_id, file_name
            )
            s3_path = f"{self.bucket}/{object_key}"

            # Create database record
            obj_db = ObjectDB(
                id=object_id,
                name=file_name,
                s3_path=s3_path,
                file_info=file_info.model_dump(),
                is_uploaded=False,
            )

            db.add(obj_db)
            db.commit()
            db.refresh(obj_db)

            return obj_db

        except SQLAlchemyError as e:
            db.rollback()
            raise ObjectServiceError(f"Failed to create object: {e}")

    def generate_presigned_upload_url(
        self,
        bucket: str,
        object_key: str,
        content_type: Optional[str] = None,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for file upload.

        Args:
            bucket: Bucket name
            object_key: Object key
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned upload URL

        Raises:
            ObjectServiceError: If URL generation fails
        """
        try:
            # Create a separate client for presigned URLs using external endpoint
            # This ensures the signature is calculated for the correct host
            external_endpoint = self.external_endpoint
            if not external_endpoint:
                raise ObjectServiceError(
                    "S3_EXTERNAL_ENDPOINT environment variable is required for presigned URLs"
                )

            external_client = boto3.client(
                "s3",
                endpoint_url=external_endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "virtual"},
                ),
            )

            params = {
                "Bucket": bucket,
                "Key": object_key,
            }
            # if content_type:
            #     params["ContentType"] = content_type

            print(f"params: {params}")
            print(f"using external endpoint: {external_endpoint}")

            presigned_url = external_client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=expires_in,
            )

            print(f"generated presigned_url: {presigned_url}")

            return presigned_url

        except ClientError as e:
            raise ObjectServiceError(f"Failed to generate presigned URL: {e}")

    def generate_presigned_upload_url_for_object(
        self,
        db: Session,
        object_id: str,
        expires_in: int = 3600,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Generate a presigned URL for file upload using object from database.

        Args:
            db: Database session
            object_id: Object ID
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned upload URL

        Raises:
            ObjectNotFoundError: If object not found
            ObjectServiceError: If URL generation fails
        """
        try:
            # Get object from database
            db_object = db.query(ObjectDB).filter(ObjectDB.id == object_id).first()
            if not db_object:
                raise ObjectNotFoundError(f"Object with ID {object_id} not found")

            s3_part = db_object.s3_path.split("/")
            bucket = s3_part[0]
            object_key = "/".join(s3_part[1:])

            print(f"bucket: {bucket}")
            print(f"object_key: {object_key}")
            print(f"content_type: {content_type}")
            print(f"expires_in: {expires_in}")

            presigned_url = self.generate_presigned_upload_url(
                bucket, object_key, content_type, expires_in
            )

            # Update object with presigned URL
            db_object.presigned_url = presigned_url
            db_object.updated_at = datetime.now(timezone.utc)
            db.commit()

            return presigned_url

        except SQLAlchemyError as e:
            db.rollback()
            raise ObjectServiceError(f"Database error: {e}")
        except ClientError as e:
            raise ObjectServiceError(f"Failed to generate presigned URL: {e}")

    def mark_uploaded(
        self, db: Session, object_id: str, file_info: Optional[FileInfo] = None
    ) -> ObjectDB:
        """
        Mark an object as uploaded.

        Args:
            db: Database session
            object_id: Object ID
            file_info: Additional file information

        Returns:
            Updated object

        Raises:
            ObjectNotFoundError: If object not found
            ObjectServiceError: If update fails
        """
        try:
            db_object = db.query(ObjectDB).filter(ObjectDB.id == object_id).first()
            if not db_object:
                raise ObjectNotFoundError(f"Object with ID {object_id} not found")

            s3_part = db_object.s3_path.split("/")
            bucket = s3_part[0]
            object_key = "/".join(s3_part[1:])

            # Verify file exists in S3
            try:
                self.s3_client.head_object(Bucket=bucket, Key=object_key)
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    raise ObjectServiceError(
                        f"File not found in S3: bucket={bucket}, object_key={object_key}"
                    )
                raise ObjectServiceError(f"S3 error: {e}")

            # Update object
            db_object.is_uploaded = True
            db_object.updated_at = datetime.now(timezone.utc)
            db_object.presigned_url = None  # Clear presigned URL

            if file_info:
                # Convert FileInfo to dict for database update
                file_info_dict = file_info.model_dump(exclude_none=True)
                if db_object.file_info is None:
                    db_object.file_info = {}
                db_object.file_info.update(file_info_dict)

            db.commit()
            db.refresh(db_object)

            return db_object

        except SQLAlchemyError as e:
            db.rollback()
            raise ObjectServiceError(f"Failed to mark object as uploaded: {e}")

    def get_object(self, db: Session, object_id: str) -> Optional[ObjectDB]:
        """
        Get an object by ID.

        Args:
            db: Database session
            object_id: Object ID

        Returns:
            Object if found, None otherwise
        """
        try:
            return db.query(ObjectDB).filter(ObjectDB.id == object_id).first()
        except SQLAlchemyError as e:
            raise ObjectServiceError(f"Failed to get object: {e}")

    def download_to_local(self, db: Session, object_id: str, local_path: str) -> str:
        """
        Download an object from S3 to local filesystem.

        Args:
            db: Database session
            object_id: Object ID
            local_path: Local file path to save the downloaded file

        Returns:
            Local file path where the file was saved

        Raises:
            ObjectNotFoundError: If object not found
            ObjectServiceError: If download fails
        """
        try:
            db_object = db.query(ObjectDB).filter(ObjectDB.id == object_id).first()
            if not db_object:
                raise ObjectNotFoundError(f"Object with ID {object_id} not found")

            if not db_object.is_uploaded:
                raise ObjectServiceError(f"Object {object_id} is not uploaded yet")

            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            if local_dir:
                Path(local_dir).mkdir(parents=True, exist_ok=True)

            s3_part = db_object.s3_path.split("/")
            bucket = s3_part[0]
            object_key = "/".join(s3_part[1:])

            # Download file from S3
            self.s3_client.download_file(
                Bucket=bucket, Key=object_key, Filename=local_path
            )

            return local_path

        except SQLAlchemyError as e:
            raise ObjectServiceError(f"Database error: {e}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise ObjectServiceError(
                    f"File not found in S3: bucket={bucket}, object_key={object_key}"
                )
            raise ObjectServiceError(f"Failed to download file: {e}")
        except Exception as e:
            raise ObjectServiceError(f"Failed to download file: {e}")

    def delete_object(
        self, db: Session, object_id: str, delete_from_s3: bool = True
    ) -> bool:
        """
        Delete an object.

        Args:
            db: Database session
            object_id: Object ID
            delete_from_s3: Whether to also delete from S3

        Returns:
            True if deleted successfully

        Raises:
            ObjectNotFoundError: If object not found
            ObjectServiceError: If deletion fails
        """
        try:
            db_object = db.query(ObjectDB).filter(ObjectDB.id == object_id).first()
            if not db_object:
                raise ObjectNotFoundError(f"Object with ID {object_id} not found")

            s3_part = db_object.s3_path.split("/")
            bucket = s3_part[0]
            object_key = "/".join(s3_part[1:])

            # Delete from S3 if requested and file is uploaded
            if delete_from_s3 and db_object.is_uploaded:
                try:
                    self.s3_client.delete_object(Bucket=bucket, Key=object_key)
                except ClientError as e:
                    # Log warning but don't fail if S3 deletion fails
                    print(f"Warning: Failed to delete from S3: {e}")

            # Delete from database
            db.delete(db_object)
            db.commit()

            return True

        except SQLAlchemyError as e:
            db.rollback()
            raise ObjectServiceError(f"Failed to delete object: {e}")

    def upload_file(self, bucket: str, object_key: str, temp_file_path: str) -> bool:
        try:
            self.s3_client.upload_file(temp_file_path, bucket, object_key)
            return True  # 上传成功返回 True
        except ClientError as e:
            print(f"Warning: Failed to upload to S3: {e}")
            return False  # 上传失败返回 False
        except Exception as e:
            print(f"Warning: Unexpected error during S3 upload: {e}")
            return False  # 其他异常也返回 False

    @classmethod
    def from_env(cls, bucket: Optional[str] = None) -> "ObjectService":
        """
        Create ObjectService instance from environment variables.

        Args:
            bucket: S3 bucket name (optional, uses S3_BUCKET env var if not provided)

        Returns:
            ObjectService instance

        Raises:
            ObjectServiceError: If required environment variables are missing
        """
        endpoint = os.getenv("S3_ENDPOINT")
        external_endpoint = os.getenv("S3_EXTERNAL_ENDPOINT")
        access_key = os.getenv("S3_ACCESS_KEY")
        secret_key = os.getenv("S3_SECRET_KEY")
        bucket = bucket or os.getenv("S3_BUCKET")
        region = os.getenv("S3_REGION")

        if not all([endpoint, access_key, secret_key, bucket]):
            missing = [
                var
                for var, val in [
                    ("S3_ENDPOINT", endpoint),
                    ("S3_ACCESS_KEY", access_key),
                    ("S3_SECRET_KEY", secret_key),
                    ("S3_BUCKET", bucket),
                ]
                if not val
            ]
            raise ObjectServiceError(
                f"Missing environment variables: {', '.join(missing)}"
            )

        return cls(
            endpoint=endpoint,  # type: ignore
            external_endpoint=external_endpoint,
            access_key=access_key,  # type: ignore
            secret_key=secret_key,  # type: ignore
            bucket=bucket,  # type: ignore
            region=region or "us-east-1",
        )
