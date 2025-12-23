"""Integration tests for Storage service."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta

from minio.error import S3Error

from app.services.storage import StorageService, storage_service


class TestStorageServiceInit:
    """Tests for StorageService initialization."""

    def test_storage_service_singleton_exists(self):
        """storage_service singleton should be created."""
        assert storage_service is not None
        assert isinstance(storage_service, StorageService)

    def test_storage_service_initial_state(self):
        """New StorageService should start uninitialized."""
        service = StorageService()
        assert service._client is None
        assert service._initialized is False


class TestStorageServiceGetClient:
    """Tests for _get_client method."""

    def test_get_client_creates_minio_client(self):
        """_get_client should create MinIO client on first call."""
        service = StorageService()

        with patch("app.services.storage.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio_class.return_value = mock_client

            client = service._get_client()

            assert client is mock_client
            mock_minio_class.assert_called_once()

    def test_get_client_reuses_existing_client(self):
        """_get_client should reuse existing client."""
        service = StorageService()
        mock_client = MagicMock()
        service._client = mock_client
        service._initialized = True

        client = service._get_client()

        assert client is mock_client


class TestEnsureBucketExists:
    """Tests for _ensure_bucket_exists method."""

    def test_creates_bucket_if_not_exists(self):
        """Should create bucket if it doesn't exist."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        service._client = mock_client
        service._initialized = False

        service._ensure_bucket_exists()

        mock_client.make_bucket.assert_called_once()
        assert service._initialized is True

    def test_skips_if_bucket_exists(self):
        """Should not create bucket if it already exists."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        service._client = mock_client
        service._initialized = False

        service._ensure_bucket_exists()

        mock_client.make_bucket.assert_not_called()
        assert service._initialized is True

    def test_handles_s3_error_gracefully(self):
        """Should handle S3Error gracefully."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.side_effect = S3Error(
            code="NoSuchBucket",
            message="Bucket not found",
            resource="test-bucket",
            request_id="123",
            host_id="host123",
            response=None,
        )
        service._client = mock_client
        service._initialized = False

        # Should not raise
        service._ensure_bucket_exists()
        assert service._initialized is False

    def test_skips_if_already_initialized(self):
        """Should skip if already initialized."""
        service = StorageService()
        mock_client = MagicMock()
        service._client = mock_client
        service._initialized = True

        service._ensure_bucket_exists()

        mock_client.bucket_exists.assert_not_called()

    def test_skips_if_client_is_none(self):
        """Should skip if client is None."""
        service = StorageService()
        service._client = None
        service._initialized = False

        service._ensure_bucket_exists()
        assert service._initialized is False


class TestUploadFile:
    """Tests for upload_file method."""

    async def test_upload_file_success(self):
        """Should upload file successfully."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        service._client = mock_client
        service._initialized = True

        result = await service.upload_file(
            file_data=b"test file content",
            filename="test.jpg",
            content_type="image/jpeg",
            folder="photos",
        )

        assert result is not None
        assert result.startswith("photos/")
        assert result.endswith(".jpg")
        mock_client.put_object.assert_called_once()

    async def test_upload_file_with_no_extension(self):
        """Should default to jpg extension if none provided."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        service._client = mock_client
        service._initialized = True

        result = await service.upload_file(
            file_data=b"test file content",
            filename="testfile",
            content_type="image/jpeg",
        )

        assert result is not None
        assert result.endswith(".jpg")

    async def test_upload_file_s3_error_returns_none(self):
        """Should return None on S3 error."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.put_object.side_effect = S3Error(
            code="InternalError",
            message="Upload failed",
            resource="test-bucket",
            request_id="123",
            host_id="host123",
            response=None,
        )
        service._client = mock_client
        service._initialized = True

        result = await service.upload_file(
            file_data=b"test file content",
            filename="test.jpg",
        )

        assert result is None


class TestGetPresignedUrl:
    """Tests for get_presigned_url method."""

    async def test_get_presigned_url_success(self):
        """Should return presigned URL."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = "https://example.com/presigned"
        service._client = mock_client
        service._initialized = True

        result = await service.get_presigned_url("photos/test.jpg")

        assert result == "https://example.com/presigned"
        mock_client.presigned_get_object.assert_called_once()

    async def test_get_presigned_url_with_custom_expiry(self):
        """Should use custom expiry time."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = "https://example.com/presigned"
        service._client = mock_client
        service._initialized = True

        await service.get_presigned_url("photos/test.jpg", expires=timedelta(hours=2))

        call_args = mock_client.presigned_get_object.call_args
        assert call_args.kwargs["expires"] == timedelta(hours=2)

    async def test_get_presigned_url_s3_error_returns_none(self):
        """Should return None on S3 error."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test-bucket",
            request_id="123",
            host_id="host123",
            response=None,
        )
        service._client = mock_client
        service._initialized = True

        result = await service.get_presigned_url("photos/nonexistent.jpg")

        assert result is None


class TestDeleteFile:
    """Tests for delete_file method."""

    async def test_delete_file_success(self):
        """Should delete file successfully."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        service._client = mock_client
        service._initialized = True

        result = await service.delete_file("photos/test.jpg")

        assert result is True
        mock_client.remove_object.assert_called_once()

    async def test_delete_file_s3_error_returns_false(self):
        """Should return False on S3 error."""
        service = StorageService()
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.remove_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test-bucket",
            request_id="123",
            host_id="host123",
            response=None,
        )
        service._client = mock_client
        service._initialized = True

        result = await service.delete_file("photos/nonexistent.jpg")

        assert result is False


class TestGetPublicUrl:
    """Tests for get_public_url method."""

    def test_get_public_url_http(self):
        """Should return HTTP URL when not secure."""
        service = StorageService()

        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.minio_secure = False
            mock_settings.minio_public_endpoint = "localhost:9000"
            service._bucket_name = "test-bucket"

            result = service.get_public_url("photos/test.jpg")

        assert result == "http://localhost:9000/test-bucket/photos/test.jpg"

    def test_get_public_url_https(self):
        """Should return HTTPS URL when secure."""
        service = StorageService()

        with patch("app.services.storage.settings") as mock_settings:
            mock_settings.minio_secure = True
            mock_settings.minio_public_endpoint = "storage.example.com"
            service._bucket_name = "test-bucket"

            result = service.get_public_url("photos/test.jpg")

        assert result == "https://storage.example.com/test-bucket/photos/test.jpg"
