"""Tests for storage service."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.storage import StorageService


class TestStorageService:
    """Tests for StorageService class."""

    @pytest.fixture
    def storage_service(self):
        """Create a StorageService instance."""
        return StorageService()

    def test_init(self, storage_service):
        """Should initialize with correct defaults."""
        assert storage_service._client is None
        assert storage_service._initialized is False

    @patch("app.services.storage.Minio")
    def test_get_client_creates_client(self, mock_minio_class, storage_service):
        """Should create MinIO client on first access."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        client = storage_service._get_client()

        assert client is mock_client
        mock_minio_class.assert_called_once()

    @patch("app.services.storage.Minio")
    def test_get_client_creates_bucket_if_not_exists(
        self, mock_minio_class, storage_service
    ):
        """Should create bucket if it doesn't exist."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = False

        storage_service._get_client()

        mock_client.make_bucket.assert_called_once()

    @patch("app.services.storage.Minio")
    def test_get_client_caches_client(self, mock_minio_class, storage_service):
        """Should cache and reuse client."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        client1 = storage_service._get_client()
        client2 = storage_service._get_client()

        assert client1 is client2
        # Only created once
        assert mock_minio_class.call_count == 1

    @patch("app.services.storage.Minio")
    async def test_upload_file_success(self, mock_minio_class, storage_service):
        """Should upload file and return path."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        result = await storage_service.upload_file(
            file_data=b"test image data",
            filename="test.jpg",
            content_type="image/jpeg",
        )

        assert result is not None
        assert result.startswith("photos/")
        assert result.endswith(".jpg")
        mock_client.put_object.assert_called_once()

    @patch("app.services.storage.Minio")
    async def test_upload_file_with_custom_folder(
        self, mock_minio_class, storage_service
    ):
        """Should upload file to custom folder."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        result = await storage_service.upload_file(
            file_data=b"test data",
            filename="document.pdf",
            content_type="application/pdf",
            folder="documents",
        )

        assert result is not None
        assert result.startswith("documents/")

    @patch("app.services.storage.Minio")
    async def test_upload_file_failure_returns_none(
        self, mock_minio_class, storage_service
    ):
        """Should return None on upload failure."""
        from minio.error import S3Error

        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.put_object.side_effect = S3Error(
            "TestError", "test", "test", "test", "test", "test"
        )

        result = await storage_service.upload_file(
            file_data=b"test data",
            filename="test.jpg",
        )

        assert result is None

    @patch("app.services.storage.Minio")
    async def test_get_presigned_url_success(self, mock_minio_class, storage_service):
        """Should return presigned URL."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = "https://example.com/presigned"

        result = await storage_service.get_presigned_url("photos/test.jpg")

        assert result == "https://example.com/presigned"

    @patch("app.services.storage.Minio")
    async def test_get_presigned_url_with_custom_expiry(
        self, mock_minio_class, storage_service
    ):
        """Should use custom expiry for presigned URL."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = "https://example.com/presigned"

        await storage_service.get_presigned_url(
            "photos/test.jpg",
            expires=timedelta(hours=24),
        )

        # Verify custom expiry was passed
        call_kwargs = mock_client.presigned_get_object.call_args[1]
        assert call_kwargs["expires"] == timedelta(hours=24)

    @patch("app.services.storage.Minio")
    async def test_get_presigned_url_failure_returns_none(
        self, mock_minio_class, storage_service
    ):
        """Should return None on presigned URL failure."""
        from minio.error import S3Error

        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.side_effect = S3Error(
            "TestError", "test", "test", "test", "test", "test"
        )

        result = await storage_service.get_presigned_url("photos/test.jpg")

        assert result is None

    @patch("app.services.storage.Minio")
    async def test_delete_file_success(self, mock_minio_class, storage_service):
        """Should delete file successfully."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        result = await storage_service.delete_file("photos/test.jpg")

        assert result is True
        mock_client.remove_object.assert_called_once()

    @patch("app.services.storage.Minio")
    async def test_delete_file_failure_returns_false(
        self, mock_minio_class, storage_service
    ):
        """Should return False on delete failure."""
        from minio.error import S3Error

        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.remove_object.side_effect = S3Error(
            "TestError", "test", "test", "test", "test", "test"
        )

        result = await storage_service.delete_file("photos/test.jpg")

        assert result is False

    @patch("app.services.storage.settings")
    def test_get_public_url(self, mock_settings, storage_service):
        """Should return correct public URL."""
        mock_settings.minio_secure = False
        mock_settings.minio_public_endpoint = "localhost:9000"
        storage_service._bucket_name = "test-bucket"

        url = storage_service.get_public_url("photos/test.jpg")

        assert url == "http://localhost:9000/test-bucket/photos/test.jpg"

    @patch("app.services.storage.settings")
    def test_get_public_url_https(self, mock_settings, storage_service):
        """Should use HTTPS when minio_secure is True."""
        mock_settings.minio_secure = True
        mock_settings.minio_public_endpoint = "storage.example.com"
        storage_service._bucket_name = "prod-bucket"

        url = storage_service.get_public_url("photos/image.png")

        assert url == "https://storage.example.com/prod-bucket/photos/image.png"

    @patch("app.services.storage.Minio")
    def test_ensure_bucket_exists_handles_s3_error(
        self, mock_minio_class, storage_service
    ):
        """Should handle S3Error gracefully when checking bucket."""
        from minio.error import S3Error

        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.side_effect = S3Error(
            "TestError", "test", "test", "test", "test", "test"
        )

        # Should not raise, just log warning
        storage_service._get_client()

        assert storage_service._initialized is False
