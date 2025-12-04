"""Ticket photo upload endpoint."""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUser, DatabaseSession
from app.core.exceptions import ForbiddenException, TicketNotFoundException
from app.models.photo import Photo, PhotoType
from app.models.user import UserRole
from app.schemas.photo import PhotoUploadResponse
from app.services.storage import storage_service
from app.services.ticket_query_service import get_ticket_by_id

router = APIRouter()


@router.post(
    "/{ticket_id}/photos",
    response_model=PhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_ticket_photo(
    ticket_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    file: UploadFile = File(...),
    photo_type: PhotoType = PhotoType.REPORT,
) -> PhotoUploadResponse:
    """Upload a photo for a ticket."""
    ticket = await get_ticket_by_id(db, ticket_id)

    if ticket is None:
        raise TicketNotFoundException()

    # Check permissions
    if photo_type == PhotoType.REPORT:
        if ticket.reporter_id != current_user.id:
            raise ForbiddenException(
                detail="Only the reporter can upload report photos"
            )
    elif photo_type == PhotoType.PROOF:
        if current_user.role not in (UserRole.SUPPORT, UserRole.MANAGER):
            raise ForbiddenException(detail="Only support can upload proof photos")

    # Upload to MinIO
    file_data = await file.read()
    object_name = await storage_service.upload_file(
        file_data,
        file.filename or "photo.jpg",
        file.content_type or "image/jpeg",
        folder=f"tickets/{ticket_id}",
    )

    if object_name is None:
        raise ForbiddenException(detail="Failed to upload photo")

    # Create photo record
    photo = Photo(
        ticket_id=ticket_id,
        url=storage_service.get_public_url(object_name),
        filename=file.filename or "photo.jpg",
        photo_type=photo_type,
        uploaded_by_id=current_user.id,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return PhotoUploadResponse(
        id=photo.id,
        url=photo.url,
        filename=photo.filename,
    )
