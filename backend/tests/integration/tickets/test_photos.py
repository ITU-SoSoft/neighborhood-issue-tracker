"""Integration tests for Ticket Photo Upload API endpoint."""

import io
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.ticket import Ticket
from tests.conftest import auth_headers


# ============================================================================
# POST /api/v1/tickets/{ticket_id}/photos - Upload photo
# ============================================================================


class TestUploadReportPhoto:
    """Tests for uploading REPORT photos (by citizens)."""

    @pytest.mark.asyncio
    async def test_reporter_can_upload_report_photo(
        self,
        client: AsyncClient,
        citizen_token: str,
        ticket: Ticket,
    ):
        """Reporter should be able to upload a REPORT photo to their own ticket."""
        fake_file = io.BytesIO(b"fake image data")

        with (
            patch(
                "app.api.v1.tickets.photos.storage_service.upload_file",
                new_callable=AsyncMock,
                return_value=f"tickets/{ticket.id}/test_photo.jpg",
            ),
            patch(
                "app.api.v1.tickets.photos.storage_service.get_public_url",
                return_value=f"http://minio:9000/tickets/{ticket.id}/test_photo.jpg",
            ),
        ):
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/photos?photo_type=REPORT",
                files={"file": ("test_photo.jpg", fake_file, "image/jpeg")},
                headers=auth_headers(citizen_token),
            )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test_photo.jpg"
        assert "url" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_reporter_upload_defaults_to_report_type(
        self,
        client: AsyncClient,
        citizen_token: str,
        ticket: Ticket,
    ):
        """Photo type should default to REPORT if not specified."""
        fake_file = io.BytesIO(b"fake image data")

        with (
            patch(
                "app.api.v1.tickets.photos.storage_service.upload_file",
                new_callable=AsyncMock,
                return_value=f"tickets/{ticket.id}/photo.jpg",
            ),
            patch(
                "app.api.v1.tickets.photos.storage_service.get_public_url",
                return_value=f"http://minio:9000/tickets/{ticket.id}/photo.jpg",
            ),
        ):
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/photos",
                files={"file": ("photo.jpg", fake_file, "image/jpeg")},
                headers=auth_headers(citizen_token),
            )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_non_reporter_cannot_upload_report_photo(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        ticket: Ticket,
    ):
        """A citizen who is not the reporter should not be able to upload REPORT photo."""
        from app.core.security import create_access_token
        from app.models.user import UserRole

        # Create another citizen who is not the reporter
        other_citizen = User(
            id=uuid.uuid4(),
            phone_number="+905559999999",
            name="Other Citizen",
            email="other_citizen@test.com",
            password_hash="hashed_password",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(other_citizen)
        await db_session.commit()

        other_citizen_token = create_access_token(data={"sub": str(other_citizen.id)})
        fake_file = io.BytesIO(b"fake image data")

        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/photos?photo_type=REPORT",
            files={"file": ("test_photo.jpg", fake_file, "image/jpeg")},
            headers=auth_headers(other_citizen_token),
        )

        assert response.status_code == 403
        assert "reporter" in response.json()["detail"].lower()


class TestUploadProofPhoto:
    """Tests for uploading PROOF photos (by staff)."""

    @pytest.mark.asyncio
    async def test_support_can_upload_proof_photo(
        self,
        client: AsyncClient,
        support_token: str,
        ticket: Ticket,
    ):
        """Support user should be able to upload a PROOF photo."""
        fake_file = io.BytesIO(b"fake proof image")

        with (
            patch(
                "app.api.v1.tickets.photos.storage_service.upload_file",
                new_callable=AsyncMock,
                return_value=f"tickets/{ticket.id}/proof.jpg",
            ),
            patch(
                "app.api.v1.tickets.photos.storage_service.get_public_url",
                return_value=f"http://minio:9000/tickets/{ticket.id}/proof.jpg",
            ),
        ):
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/photos?photo_type=PROOF",
                files={"file": ("proof.jpg", fake_file, "image/jpeg")},
                headers=auth_headers(support_token),
            )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "proof.jpg"

    @pytest.mark.asyncio
    async def test_manager_can_upload_proof_photo(
        self,
        client: AsyncClient,
        manager_token: str,
        ticket: Ticket,
    ):
        """Manager should be able to upload a PROOF photo."""
        fake_file = io.BytesIO(b"fake proof image")

        with (
            patch(
                "app.api.v1.tickets.photos.storage_service.upload_file",
                new_callable=AsyncMock,
                return_value=f"tickets/{ticket.id}/manager_proof.jpg",
            ),
            patch(
                "app.api.v1.tickets.photos.storage_service.get_public_url",
                return_value=f"http://minio:9000/tickets/{ticket.id}/manager_proof.jpg",
            ),
        ):
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/photos?photo_type=PROOF",
                files={"file": ("manager_proof.jpg", fake_file, "image/jpeg")},
                headers=auth_headers(manager_token),
            )

        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "manager_proof.jpg"

    @pytest.mark.asyncio
    async def test_citizen_cannot_upload_proof_photo(
        self,
        client: AsyncClient,
        citizen_token: str,
        ticket: Ticket,
    ):
        """Citizen should not be able to upload a PROOF photo."""
        fake_file = io.BytesIO(b"fake proof image")

        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/photos?photo_type=PROOF",
            files={"file": ("proof.jpg", fake_file, "image/jpeg")},
            headers=auth_headers(citizen_token),
        )

        assert response.status_code == 403
        assert "support" in response.json()["detail"].lower()


class TestPhotoUploadErrors:
    """Tests for error cases in photo upload."""

    @pytest.mark.asyncio
    async def test_upload_to_nonexistent_ticket_returns_404(
        self,
        client: AsyncClient,
        citizen_token: str,
    ):
        """Uploading to a non-existent ticket should return 404."""
        fake_file = io.BytesIO(b"fake image data")
        fake_ticket_id = uuid.uuid4()

        response = await client.post(
            f"/api/v1/tickets/{fake_ticket_id}/photos",
            files={"file": ("test.jpg", fake_file, "image/jpeg")},
            headers=auth_headers(citizen_token),
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_upload_returns_401(
        self,
        client: AsyncClient,
        ticket: Ticket,
    ):
        """Unauthenticated request should return 401."""
        fake_file = io.BytesIO(b"fake image data")

        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/photos",
            files={"file": ("test.jpg", fake_file, "image/jpeg")},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_storage_failure_returns_error(
        self,
        client: AsyncClient,
        citizen_token: str,
        ticket: Ticket,
    ):
        """Storage service failure should return an error."""
        fake_file = io.BytesIO(b"fake image data")

        with patch(
            "app.api.v1.tickets.photos.storage_service.upload_file",
            new_callable=AsyncMock,
            return_value=None,  # Simulate upload failure
        ):
            response = await client.post(
                f"/api/v1/tickets/{ticket.id}/photos",
                files={"file": ("test.jpg", fake_file, "image/jpeg")},
                headers=auth_headers(citizen_token),
            )

        assert response.status_code == 403
        assert "failed" in response.json()["detail"].lower()
