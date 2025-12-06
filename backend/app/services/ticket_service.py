"""Ticket service for business logic."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.exceptions import (
    CategoryNotFoundException,
    ForbiddenException,
    InvalidStatusTransitionException,
    TicketNotFoundException,
)
from app.models.category import Category
from app.models.ticket import Location, StatusLog, Ticket, TicketFollower, TicketStatus
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.ticket_query_service import VALID_TRANSITIONS


class TicketService:
    """Service for ticket business logic."""

    async def create_ticket(
        self,
        db: AsyncSession,
        request: TicketCreate,
        current_user: User,
    ) -> Ticket:
        """Create a new ticket.

        Args:
            db: Database session.
            request: Ticket creation data.
            current_user: The user creating the ticket.

        Returns:
            The created ticket with loaded relationships.

        Raises:
            CategoryNotFoundException: If the category doesn't exist or is inactive.
        """
        # Verify category exists
        result = await db.execute(
            select(Category).where(
                Category.id == request.category_id,
                Category.is_active == True,  # noqa: E712
            )
        )
        category = result.scalar_one_or_none()
        if category is None:
            raise CategoryNotFoundException()

        # Create location with PostGIS point
        location = Location(
            latitude=request.location.latitude,
            longitude=request.location.longitude,
            address=request.location.address,
            district=request.location.district,
            city=request.location.city,
            coordinates=f"POINT({request.location.longitude} {request.location.latitude})",
        )
        db.add(location)
        await db.flush()

        # Create ticket
        ticket = Ticket(
            title=request.title,
            description=request.description,
            category_id=request.category_id,
            location_id=location.id,
            reporter_id=current_user.id,
            status=TicketStatus.NEW,
        )
        db.add(ticket)
        await db.flush()  # Flush to get ticket.id for related objects

        # Auto-follow the ticket
        follower = TicketFollower(
            ticket_id=ticket.id,
            user_id=current_user.id,
        )
        db.add(follower)

        # Create initial status log
        status_log = StatusLog(
            ticket_id=ticket.id,
            old_status=None,
            new_status=TicketStatus.NEW.value,
            changed_by_id=current_user.id,
        )
        db.add(status_log)

        await db.commit()
        await db.refresh(ticket)

        # Send notification
        from app.services.notification_service import notify_ticket_created

        try:
            await notify_ticket_created(db, ticket)
        except Exception:
            # Don't fail ticket creation if notification fails
            pass

        # Load relationships
        result = await db.execute(
            select(Ticket)
            .options(
                joinedload(Ticket.category),
                joinedload(Ticket.location),
                joinedload(Ticket.reporter),
                selectinload(Ticket.photos),
                selectinload(Ticket.comments),
                selectinload(Ticket.followers),
            )
            .where(Ticket.id == ticket.id)
        )
        return result.scalar_one()

    async def update_ticket(
        self,
        db: AsyncSession,
        ticket: Ticket,
        request: TicketUpdate,
        current_user: User,
    ) -> Ticket:
        """Update ticket details (title, description, category).

        Args:
            db: Database session.
            ticket: The ticket to update (with loaded relationships).
            request: Update data.
            current_user: The user making the update.

        Returns:
            The updated ticket.

        Raises:
            ForbiddenException: If user doesn't have permission.
            CategoryNotFoundException: If new category doesn't exist.
        """
        # Permission checks
        is_reporter = ticket.reporter_id == current_user.id
        is_staff = current_user.role in (UserRole.SUPPORT, UserRole.MANAGER)

        if not is_reporter and not is_staff:
            raise ForbiddenException(
                detail="You don't have permission to update this ticket"
            )

        # Citizens can only update NEW tickets
        if is_reporter and not is_staff and ticket.status != TicketStatus.NEW:
            raise ForbiddenException(
                detail="You can only update tickets that are still NEW"
            )

        # No one can update CLOSED tickets
        if ticket.status == TicketStatus.CLOSED:
            raise ForbiddenException(detail="Cannot update a closed ticket")

        # If category is being changed, verify it exists
        if request.category_id:
            result = await db.execute(
                select(Category).where(
                    Category.id == request.category_id,
                    Category.is_active == True,  # noqa: E712
                )
            )
            category = result.scalar_one_or_none()
            if category is None:
                raise CategoryNotFoundException()

        # Update fields
        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ticket, field, value)

        await db.commit()
        await db.refresh(ticket)

        return ticket

    async def update_status(
        self,
        db: AsyncSession,
        ticket: Ticket,
        new_status: TicketStatus,
        comment: str | None,
        current_user: User,
    ) -> Ticket:
        """Update ticket status with validation.

        Args:
            db: Database session.
            ticket: The ticket to update.
            new_status: The new status.
            comment: Optional comment for the status change.
            current_user: The user making the change.

        Returns:
            The updated ticket.

        Raises:
            InvalidStatusTransitionException: If the transition is not allowed.
        """
        # Validate transition
        allowed = VALID_TRANSITIONS.get(ticket.status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionException(
                ticket.status.value, new_status.value
            )

        old_status = ticket.status
        ticket.status = new_status

        # Set resolved_at if transitioning to resolved
        if new_status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.now(timezone.utc)

        # Create status log
        status_log = StatusLog(
            ticket_id=ticket.id,
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by_id=current_user.id,
            comment=comment,
        )
        db.add(status_log)

        await db.commit()
        await db.refresh(ticket)

        # Send notification
        from app.services.notification_service import notify_ticket_status_changed

        try:
            await notify_ticket_status_changed(db, ticket, old_status, new_status, current_user)
        except Exception:
            # Don't fail status update if notification fails
            pass

        return ticket

    async def assign_ticket(
        self,
        db: AsyncSession,
        ticket: Ticket,
        assignee_id: UUID,
    ) -> Ticket:
        """Assign a ticket to a support member.

        Args:
            db: Database session.
            ticket: The ticket to assign.
            assignee_id: The user ID to assign the ticket to.

        Returns:
            The updated ticket.

        Raises:
            ForbiddenException: If the assignee is not a valid support/manager user.
        """
        # Verify assignee exists and is support/manager
        result = await db.execute(
            select(User).where(
                User.id == assignee_id,
                User.deleted_at.is_(None),
                User.role.in_([UserRole.SUPPORT, UserRole.MANAGER]),
            )
        )
        assignee = result.scalar_one_or_none()

        if assignee is None:
            raise ForbiddenException(detail="Invalid assignee")

        ticket.assignee_id = assignee_id

        await db.commit()
        await db.refresh(ticket)

        return ticket


# Singleton instance
ticket_service = TicketService()
