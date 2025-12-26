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
    NotFoundException,
    TicketNotFoundException,
)
from app.models.category import Category
from app.models.district import District
from app.models.ticket import Location, StatusLog, Ticket, TicketFollower, TicketStatus
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.ticket_query_service import VALID_TRANSITIONS
from app.services.team_assignment_service import TeamAssignmentService


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
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Creating ticket: {request.title}")
        logger.info(f"  Category ID: {request.category_id}")
        logger.info(f"  Location - district_id: {request.location.district_id}")
        logger.info(
            f"  Location - coordinates: ({request.location.latitude}, {request.location.longitude})"
        )

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

        # Handle location creation based on input type
        district_name = None
        city = request.location.city

        if request.location.district_id:
            # Get district details from database
            district_result = await db.execute(
                select(District).where(District.id == request.location.district_id)
            )
            district_obj = district_result.scalar_one_or_none()
            if not district_obj:
                raise NotFoundException(
                    f"District with id {request.location.district_id} not found"
                )

            district_name = district_obj.name
            city = district_obj.city
            # Use default coordinates for district center (approximate)
            latitude = 41.0082  # Istanbul center
            longitude = 28.9784
        else:
            # Use provided GPS coordinates
            latitude = request.location.latitude
            longitude = request.location.longitude

        # Create location with PostGIS point
        location = Location(
            latitude=latitude,
            longitude=longitude,
            address=request.location.address,
            district=district_name,
            city=city,
            coordinates=f"POINT({longitude} {latitude})",
        )
        db.add(location)
        await db.flush()

        # Find matching team for automatic assignment
        assignment_service = TeamAssignmentService()
        assigned_team = await assignment_service.find_matching_team(
            session=db,
            category_id=request.category_id,
            district=district_name,
            city=city,
        )

        # Create ticket
        ticket = Ticket(
            title=request.title,
            description=request.description,
            category_id=request.category_id,
            location_id=location.id,
            reporter_id=current_user.id,
            team_id=assigned_team.id if assigned_team else None,
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

        # Reload ticket with all relationships to avoid lazy loading issues
        from app.models.comment import Comment

        result = await db.execute(
            select(Ticket)
            .where(Ticket.id == ticket.id)
            .options(
                joinedload(Ticket.category),
                joinedload(Ticket.location),
                joinedload(Ticket.reporter),
                joinedload(Ticket.assigned_team),
                selectinload(Ticket.photos),
                selectinload(Ticket.comments).joinedload(Comment.user),
                selectinload(Ticket.followers),
            )
        )
        ticket = result.scalar_one()

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
                joinedload(Ticket.assigned_team),
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
            ForbiddenException: If support user tries to update ticket from another team.
        """
        # Support users can only update tickets from their own team
        if current_user.role == UserRole.SUPPORT:
            if ticket.team_id is None:
                raise ForbiddenException(
                    detail="Cannot update status of unassigned tickets"
                )
            if ticket.team_id != current_user.team_id:
                raise ForbiddenException(
                    detail="You can only update status of tickets assigned to your team"
                )

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
            await notify_ticket_status_changed(
                db, ticket, old_status, new_status, current_user
            )
        except Exception:
            # Don't fail status update if notification fails
            pass

        return ticket

    async def assign_ticket(
        self,
        db: AsyncSession,
        ticket: Ticket,
        team_id: UUID,
    ) -> Ticket:
        """Assign a ticket to a team.

        Args:
            db: Database session.
            ticket: The ticket to assign.
            team_id: The team ID to assign the ticket to.

        Returns:
            The updated ticket.

        Raises:
            NotFoundException: If the team doesn't exist.
        """
        # Verify team exists
        from app.models.team import Team

        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if team is None:
            raise NotFoundException(f"Team with id {team_id} not found")

        ticket.team_id = team_id

        await db.commit()
        await db.refresh(ticket)

        return ticket

    async def delete_ticket(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        current_user: User,
    ) -> None:
        """Soft delete a ticket.

        Citizens can only delete their own tickets if status is NEW.

        Args:
            db: Database session.
            ticket_id: The ticket ID to delete.
            current_user: The user requesting deletion.

        Raises:
            TicketNotFoundException: If ticket doesn't exist.
            ForbiddenException: If user doesn't have permission.
        """
        # Fetch the ticket
        result = await db.execute(
            select(Ticket).where(
                Ticket.id == ticket_id,
                Ticket.deleted_at.is_(None),
            )
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise TicketNotFoundException()

        # Permission check: only reporter can delete
        if ticket.reporter_id != current_user.id:
            raise ForbiddenException(detail="You can only delete your own tickets")

        # Only NEW tickets can be deleted
        if ticket.status != TicketStatus.NEW:
            raise ForbiddenException(
                detail="You can only delete tickets with NEW status"
            )

        # Soft delete
        ticket.deleted_at = datetime.now(timezone.utc)
        await db.commit()


# Singleton instance
ticket_service = TicketService()
