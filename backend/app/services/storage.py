"""Storage service for file uploads using MinIO."""

import logging
import uuid
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for file storage using MinIO."""

    def __init__(self) -> None:
        """Initialize the storage service."""
        self._client: Minio | None = None
        self._bucket_name = settings.minio_bucket_name
        self._initialized = False

    def _get_client(self) -> Minio:
        """Get or create the MinIO client (lazy initialization)."""
        if self._client is None:
            self._client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
            self._ensure_bucket_exists()
        return self._client

    def _ensure_bucket_exists(self) -> None:
        """Ensure the storage bucket exists."""
        if self._initialized or self._client is None:
            return
        try:
            if not self._client.bucket_exists(self._bucket_name):
                self._client.make_bucket(self._bucket_name)
                logger.info(f"Created bucket: {self._bucket_name}")
            self._initialized = True
        except S3Error as e:
            logger.warning(f"MinIO not available, storage disabled: {e}")

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "image/jpeg",
        folder: str = "photos",
    ) -> str | None:
        """Upload a file to storage.

        Args:
            file_data: The file content as bytes.
            filename: The original filename.
            content_type: The MIME type of the file.
            folder: The folder path within the bucket.

        Returns:
            The URL of the uploaded file, or None if upload failed.
        """
        try:
            # Generate unique filename
            ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
            unique_filename = f"{folder}/{uuid.uuid4()}.{ext}"

            # Upload to MinIO
            client = self._get_client()
            client.put_object(
                self._bucket_name,
                unique_filename,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )

            logger.info(f"Uploaded file: {unique_filename}")
            return unique_filename
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            return None

    async def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
    ) -> str | None:
        """Get a presigned URL for accessing a file.

        Args:
            object_name: The object name/path in storage.
            expires: How long the URL should be valid.

        Returns:
            The presigned URL, or None if generation failed.
        """
        try:
            client = self._get_client()
            url = client.presigned_get_object(
                self._bucket_name,
                object_name,
                expires=expires,
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    async def delete_file(self, object_name: str) -> bool:
        """Delete a file from storage.

        Args:
            object_name: The object name/path to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            client = self._get_client()
            client.remove_object(self._bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def get_public_url(self, object_name: str) -> str:
        """Get the public URL for an object.

        Note: This assumes the bucket has public read access configured.
        Uses minio_public_endpoint for browser-accessible URLs.

        Args:
            object_name: The object name/path.

        Returns:
            The public URL.
        """
        protocol = "https" if settings.minio_secure else "http"
        # Use public endpoint for browser access (not internal Docker network)
        public_endpoint = settings.minio_public_endpoint
        return f"{protocol}://{public_endpoint}/{self._bucket_name}/{object_name}"


# Singleton instance
storage_service = StorageService()
