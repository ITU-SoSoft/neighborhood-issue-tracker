"""Team management API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_async_session, get_current_user, get_manager_user
from app.core.exceptions import ConflictException, NotFoundException
from app.models import Team, User
from app.schemas.team import (
    TeamCreate,
    TeamDetailResponse,
    TeamListResponse,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)

router = APIRouter()

DatabaseSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ManagerUser = Annotated[User, Depends(get_manager_user)]


async def _get_team_with_members(db: AsyncSession, team_id: uuid.UUID) -> Team | None:
    """Helper: fetch a team with members eagerly loaded."""
    stmt = (
        select(Team)
        .options(selectinload(Team.members))
        .where(Team.id == team_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _to_team_response(team: Team, member_count: int = 0, active_ticket_count: int = 0) -> TeamResponse:
    """Helper: convert Team ORM object to TeamResponse."""
    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=member_count,
        active_ticket_count=active_ticket_count,
    )


def _to_team_detail_response(team: Team) -> TeamDetailResponse:
    """Helper: convert Team ORM object to TeamDetailResponse."""
    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=len([m for m in team.members if m.deleted_at is None]),
        active_ticket_count=0,  # Workload kısmında hesaplarız
        members=[
            TeamMemberResponse(
                id=member.id,
                name=member.name,
                email=member.email,
                role=member.role.value,
            )
            for member in team.members
            if member.deleted_at is None
        ],
        districts=[],   # Şimdilik boş; istersen sonraki adımda ekleriz
        categories=[],  # Şimdilik boş; istersen sonraki adımda ekleriz
    )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    db: DatabaseSession,
    _: ManagerUser,
) -> TeamListResponse:
    """List all teams with member count (non-deleted members).

    Only accessible by managers.
    """
    stmt = (
        select(Team, func.count(User.id).label("member_count"))
        .outerjoin(User, (User.team_id == Team.id) & (User.deleted_at.is_(None)))
        .group_by(Team.id)
        .order_by(Team.name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items: list[TeamResponse] = [
        _to_team_response(team, member_count=member_count, active_ticket_count=0)
        for team, member_count in rows
    ]

    return TeamListResponse(
        items=items,
        total=len(items),
        page=1,
        page_size=20,
    )


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: uuid.UUID,
    db: DatabaseSession,
    _: ManagerUser,
) -> TeamDetailResponse:
    """Get team details including members.

    Only accessible by managers.
    """
    team = await _get_team_with_members(db, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    return _to_team_detail_response(team)


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: DatabaseSession,
    _: ManagerUser,
) -> TeamResponse:
    """Create a new team.

    Only accessible by managers.
    """
    existing = await db.execute(select(Team).where(Team.name == team_data.name))
    if existing.scalar_one_or_none():
        raise ConflictException(detail="Team with this name already exists")

    team = Team(
        name=team_data.name,
        description=team_data.description,
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return _to_team_response(team, member_count=0, active_ticket_count=0)


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    team_data: TeamUpdate,
    db: DatabaseSession,
    _: ManagerUser,
) -> TeamResponse:
    """Update a team.

    Only accessible by managers.
    """
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    if team_data.name and team_data.name != team.name:
        existing = await db.execute(select(Team).where(Team.name == team_data.name))
        if existing.scalar_one_or_none():
            raise ConflictException(detail="Team with this name already exists")

    update_data = team_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.commit()
    await db.refresh(team)

    # member_count'i güncel sayalım
    result = await db.execute(
        select(func.count(User.id))
        .where((User.team_id == team.id) & (User.deleted_at.is_(None)))
    )
    member_count = int(result.scalar() or 0)

    return _to_team_response(team, member_count=member_count, active_ticket_count=0)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: uuid.UUID,
    db: DatabaseSession,
    _: ManagerUser,
) -> None:
    """Delete a team.

    Only accessible by managers.

    Note: Members will have team_id set to NULL before deleting the team.
    """
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    # Set team_id = NULL for all users in this team
    await db.execute(update(User).where(User.team_id == team_id).values(team_id=None))
    await db.commit()

    await db.delete(team)
    await db.commit()


@router.post("/{team_id}/members/{user_id}", response_model=TeamDetailResponse)
async def add_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DatabaseSession,
    _: ManagerUser,
) -> TeamDetailResponse:
    """Add a user to a team.

    Only accessible by managers.
    """
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundException(detail="User not found")

    if user.team_id == team_id:
        team_full = await _get_team_with_members(db, team_id)
        return _to_team_detail_response(team_full)  # type: ignore[arg-type]

    user.team_id = team_id
    await db.commit()

    team_full = await _get_team_with_members(db, team_id)
    if not team_full:
        raise NotFoundException(detail="Team not found")

    return _to_team_detail_response(team_full)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DatabaseSession,
    _: ManagerUser,
) -> None:
    """Remove a user from a team.

    Only accessible by managers.
    """
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundException(detail="User not found")

    if user.team_id != team_id:
        raise NotFoundException(detail="User is not a member of this team")

    user.team_id = None
    await db.commit()
