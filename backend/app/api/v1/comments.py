"""Comment API routes."""

from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, DatabaseSession
from app.core.exceptions import ForbiddenException, TicketNotFoundException
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import UserRole
from app.schemas.comment import CommentCreate, CommentListResponse, CommentResponse

router = APIRouter()


@router.get(
    "/{ticket_id}/comments",
    response_model=CommentListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_comments(
    ticket_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CommentListResponse:
    """List comments for a ticket.

    Citizens can only see public comments.
    Support/managers can see all comments.
    """
    # Verify ticket exists
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.deleted_at.is_(None))
    )
    if result.scalar_one_or_none() is None:
        raise TicketNotFoundException()

    # Build query
    query = (
        select(Comment)
        .options(joinedload(Comment.user))
        .where(Comment.ticket_id == ticket_id)
    )

    # Filter internal comments for citizens
    if current_user.role == UserRole.CITIZEN:
        query = query.where(Comment.is_internal == False)  # noqa: E712

    query = query.order_by(Comment.created_at.desc())  # Most recent first

    result = await db.execute(query)
    comments = result.scalars().all()

    return CommentListResponse(
        items=[
            CommentResponse(
                id=c.id,
                ticket_id=c.ticket_id,
                user_id=c.user_id,
                user_name=c.user.name if c.user else None,
                content=c.content,
                is_internal=c.is_internal,
                created_at=c.created_at,
            )
            for c in comments
        ],
        total=len(comments),
    )


@router.post(
    "/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    ticket_id: UUID,
    request: CommentCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CommentResponse:
    """Add a comment to a ticket.

    All authenticated users can add public comments.
    Only support/managers can add internal comments.
    """
    # Citizens cannot create internal comments
    if request.is_internal and current_user.role == UserRole.CITIZEN:
        raise ForbiddenException(detail="Citizens cannot create internal comments")

    # Verify ticket exists
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.deleted_at.is_(None))
    )
    if result.scalar_one_or_none() is None:
        raise TicketNotFoundException()

    # Get ticket for notification
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one()
    
    comment = Comment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        content=request.content,
        is_internal=request.is_internal,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Send notification for public comments only
    if not comment.is_internal:
        from app.services.notification_service import notify_comment_added
        
        try:
            await notify_comment_added(db, ticket, current_user, comment.content)
        except Exception:
            # Don't fail comment creation if notification fails
            pass

    return CommentResponse(
        id=comment.id,
        ticket_id=comment.ticket_id,
        user_id=comment.user_id,
        user_name=current_user.name,
        content=comment.content,
        is_internal=comment.is_internal,
        created_at=comment.created_at,
    )
