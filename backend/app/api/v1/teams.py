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


def _to_team_detail_response(team: Team) -> TeamDetailResponse:
    """Helper: convert Team ORM object to TeamDetailResponse."""
    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at,
        updated_at=team.updated_at,
        members=[
            TeamMemberResponse(
                id=member.id,
                name=member.name,
                phone_number=member.phone_number,
                role=member.role.value,
            )
            for member in team.members
            if member.deleted_at is None
        ],
    )


@router.get("", response_model=list[TeamListResponse])
async def list_teams(
    db: DatabaseSession,
    _: ManagerUser,
) -> list[TeamListResponse]:
    """List all teams with member count.

    Only accessible by managers.
    """
    # Count only active (non-soft-deleted) members
    stmt = (
        select(Team, func.count(User.id).label("member_count"))
        .outerjoin(User, (User.team_id == Team.id) & (User.deleted_at.is_(None)))
        .group_by(Team.id)
        .order_by(Team.name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        TeamListResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            member_count=member_count,
        )
        for team, member_count in rows
    ]


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

    return TeamResponse.model_validate(team)


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

    return TeamResponse.model_validate(team)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: uuid.UUID,
    db: DatabaseSession,
    _: ManagerUser,
) -> None:
    """Delete a team.

    Only accessible by managers.

    Note: Members will have team_id set to NULL before deleting the team
    (safer than relying only on FK ondelete settings).
    """
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    # Set team_id = NULL for all users in this team
    await db.execute(
        update(User).where(User.team_id == team_id).values(team_id=None)
    )
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

    # Optional: if user is already in this team, just return current team detail
    if user.team_id == team_id:
        team_full = await _get_team_with_members(db, team_id)
        # team_full is guaranteed to exist since we checked above
        return _to_team_detail_response(team_full)  # type: ignore[arg-type]

    user.team_id = team_id
    await db.commit()

    # IMPORTANT: reload team with members after commit so response is up-to-date
    team_full = await _get_team_with_members(db, team_id)
    return _to_team_detail_response(team_full)  # type: ignore[arg-type]


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
