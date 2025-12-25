"""Escalation API routes."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import DatabaseSession, ManagerUser, SupportUser
from app.core.exceptions import (
    EscalationAlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    TicketNotFoundException,
)
from app.models.escalation import EscalationRequest, EscalationStatus
from app.models.ticket import StatusLog, Ticket, TicketStatus
from app.models.user import UserRole
from app.schemas.escalation import (
    EscalationCreate,
    EscalationListResponse,
    EscalationResponse,
    EscalationReview,
)

router = APIRouter()


def _build_escalation_response(escalation: EscalationRequest) -> EscalationResponse:
    """Build an escalation response."""
    return EscalationResponse(
        id=escalation.id,
        ticket_id=escalation.ticket_id,
        ticket_title=escalation.ticket.title if escalation.ticket else None,
        requester_id=escalation.requester_id,
        requester_name=escalation.requester.name if escalation.requester else None,
        reviewer_id=escalation.reviewer_id,
        reviewer_name=escalation.reviewer.name if escalation.reviewer else None,
        reason=escalation.reason,
        status=escalation.status,
        review_comment=escalation.review_comment,
        created_at=escalation.created_at,
        reviewed_at=escalation.reviewed_at,
    )


@router.post(
    "",
    response_model=EscalationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_escalation(
    request: EscalationCreate,
    current_user: SupportUser,
    db: DatabaseSession,
) -> EscalationResponse:
    """Create an escalation request (support only)."""
    # Verify ticket exists and load escalations
    result = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.escalations))
        .where(Ticket.id == request.ticket_id, Ticket.deleted_at.is_(None))
    )
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise TicketNotFoundException()

    # Check if ticket is assigned to a team
    if ticket.team_id is None:
        raise ForbiddenException(detail="Cannot escalate unassigned tickets")

    # Check if support user belongs to the ticket's team
    if ticket.team_id != current_user.team_id:
        raise ForbiddenException(detail="You can only escalate tickets assigned to your team")

    # Check for existing escalations that block new creation
    has_pending = any(e.status == EscalationStatus.PENDING for e in ticket.escalations)
    has_approved = any(e.status == EscalationStatus.APPROVED for e in ticket.escalations)

    if has_pending:
        raise EscalationAlreadyExistsException()

    if has_approved:
        raise ForbiddenException(detail="Ticket escalation already approved")

    # Create escalation (allowed if no escalations or only rejected ones exist)
    escalation = EscalationRequest(
        ticket_id=request.ticket_id,
        requester_id=current_user.id,
        reason=request.reason,
        status=EscalationStatus.PENDING,
    )
    db.add(escalation)

    # Update ticket status
    old_status = ticket.status
    ticket.status = TicketStatus.ESCALATED

    # Create status log
    status_log = StatusLog(
        ticket_id=ticket.id,
        old_status=old_status.value,
        new_status=TicketStatus.ESCALATED.value,
        changed_by_id=current_user.id,
        comment=f"Escalated: {request.reason[:100]}",
    )
    db.add(status_log)

    await db.commit()
    await db.refresh(escalation)

    # Load relationships
    result = await db.execute(
        select(EscalationRequest)
        .options(
            joinedload(EscalationRequest.ticket),
            joinedload(EscalationRequest.requester),
        )
        .where(EscalationRequest.id == escalation.id)
    )
    escalation = result.scalar_one()

    # Send notification to managers
    from app.services.notification_service import notify_escalation_requested
    
    try:
        await notify_escalation_requested(db, ticket, request.reason, current_user)
    except Exception:
        # Don't fail escalation creation if notification fails
        pass

    return _build_escalation_response(escalation)


@router.get(
    "",
    response_model=EscalationListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_escalations(
    current_user: SupportUser,
    db: DatabaseSession,
    status_filter: EscalationStatus | None = None,
    ticket_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> EscalationListResponse:
    """List escalation requests (support sees own team, managers see all)."""
    # Build base query with join to Ticket for team filtering
    query = select(EscalationRequest).join(Ticket)

    # Role-based filtering: support users only see their team's escalations
    if current_user.role == UserRole.SUPPORT:
        if current_user.team_id is None:
            # Support user without team can't see any escalations
            return EscalationListResponse(items=[], total=0)
        query = query.where(Ticket.team_id == current_user.team_id)
    # Managers see all escalations (no additional filter)

    if status_filter:
        query = query.where(EscalationRequest.status == status_filter)

    # Filter by ticket_id if provided (for viewing escalation history of a specific ticket)
    if ticket_id:
        query = query.where(EscalationRequest.ticket_id == ticket_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = (
        query.options(
            joinedload(EscalationRequest.ticket),
            joinedload(EscalationRequest.requester),
            joinedload(EscalationRequest.reviewer),
        )
        .order_by(EscalationRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    escalations = result.unique().scalars().all()

    return EscalationListResponse(
        items=[_build_escalation_response(e) for e in escalations],
        total=total,
    )


@router.get(
    "/{escalation_id}",
    response_model=EscalationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_escalation(
    escalation_id: UUID,
    current_user: SupportUser,
    db: DatabaseSession,
) -> EscalationResponse:
    """Get an escalation request by ID."""
    result = await db.execute(
        select(EscalationRequest)
        .options(
            joinedload(EscalationRequest.ticket),
            joinedload(EscalationRequest.requester),
            joinedload(EscalationRequest.reviewer),
        )
        .where(EscalationRequest.id == escalation_id)
    )
    escalation = result.scalar_one_or_none()

    if escalation is None:
        raise NotFoundException(detail="Escalation not found")

    return _build_escalation_response(escalation)


@router.patch(
    "/{escalation_id}/approve",
    response_model=EscalationResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_escalation(
    escalation_id: UUID,
    request: EscalationReview,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> EscalationResponse:
    """Approve an escalation request (manager only)."""
    result = await db.execute(
        select(EscalationRequest)
        .options(
            joinedload(EscalationRequest.ticket),
            joinedload(EscalationRequest.requester),
        )
        .where(EscalationRequest.id == escalation_id)
    )
    escalation = result.scalar_one_or_none()

    if escalation is None:
        raise NotFoundException(detail="Escalation not found")

    if escalation.status != EscalationStatus.PENDING:
        raise ForbiddenException(detail="Escalation has already been reviewed")

    # Update escalation
    escalation.status = EscalationStatus.APPROVED
    escalation.reviewer_id = current_user.id
    escalation.review_comment = request.comment
    escalation.reviewed_at = datetime.now(timezone.utc)

    # Update ticket status back to in_progress
    if escalation.ticket:
        escalation.ticket.status = TicketStatus.IN_PROGRESS

        # Create status log
        status_log = StatusLog(
            ticket_id=escalation.ticket.id,
            old_status=TicketStatus.ESCALATED.value,
            new_status=TicketStatus.IN_PROGRESS.value,
            changed_by_id=current_user.id,
            comment=f"Escalation approved: {request.comment or 'No comment'}",
        )
        db.add(status_log)

    await db.commit()
    await db.refresh(escalation)

    # Send notification to reporter and requester
    from app.services.notification_service import notify_escalation_decision
    
    try:
        if escalation.ticket:
            await notify_escalation_decision(db, escalation.ticket, approved=True, decided_by=current_user)
    except Exception:
        # Don't fail approval if notification fails
        pass

    return _build_escalation_response(escalation)


@router.patch(
    "/{escalation_id}/reject",
    response_model=EscalationResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_escalation(
    escalation_id: UUID,
    request: EscalationReview,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> EscalationResponse:
    """Reject an escalation request (manager only)."""
    result = await db.execute(
        select(EscalationRequest)
        .options(
            joinedload(EscalationRequest.ticket),
            joinedload(EscalationRequest.requester),
        )
        .where(EscalationRequest.id == escalation_id)
    )
    escalation = result.scalar_one_or_none()

    if escalation is None:
        raise NotFoundException(detail="Escalation not found")

    if escalation.status != EscalationStatus.PENDING:
        raise ForbiddenException(detail="Escalation has already been reviewed")

    # Update escalation
    escalation.status = EscalationStatus.REJECTED
    escalation.reviewer_id = current_user.id
    escalation.review_comment = request.comment
    escalation.reviewed_at = datetime.now(timezone.utc)

    # Update ticket status back to in_progress
    if escalation.ticket:
        escalation.ticket.status = TicketStatus.IN_PROGRESS

        # Create status log
        status_log = StatusLog(
            ticket_id=escalation.ticket.id,
            old_status=TicketStatus.ESCALATED.value,
            new_status=TicketStatus.IN_PROGRESS.value,
            changed_by_id=current_user.id,
            comment=f"Escalation rejected: {request.comment or 'No comment'}",
        )
        db.add(status_log)

    await db.commit()
    await db.refresh(escalation)

    # Send notification to reporter and requester
    from app.services.notification_service import notify_escalation_decision
    
    try:
        if escalation.ticket:
            await notify_escalation_decision(db, escalation.ticket, approved=False, decided_by=current_user)
    except Exception:
        # Don't fail rejection if notification fails
        pass

    return _build_escalation_response(escalation)
