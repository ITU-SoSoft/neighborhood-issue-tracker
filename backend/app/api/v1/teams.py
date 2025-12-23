"""Team management API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_async_session, get_current_user, get_manager_user
from app.core.exceptions import ConflictException, NotFoundException
from app.models import Team, User
from app.models.team import TeamCategory, TeamDistrict
from app.schemas.team import (
    TeamCreate,
    TeamDetailResponse,
    TeamListResponse,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
    UnassignedMemberResponse,
)

router = APIRouter()

DatabaseSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ManagerUser = Annotated[User, Depends(get_manager_user)]


async def _get_team_with_members(db: AsyncSession, team_id: uuid.UUID) -> Team | None:
    """Helper: fetch a team with members, categories, and districts eagerly loaded."""
    stmt = (
        select(Team)
        .options(
            selectinload(Team.members),
            selectinload(Team.team_categories).selectinload(TeamCategory.category),
            selectinload(Team.team_districts).selectinload(TeamDistrict.district),
        )
        .where(Team.id == team_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _to_team_detail_response(team: Team) -> TeamDetailResponse:
    """Helper: convert Team ORM object to TeamDetailResponse."""
    from app.schemas.team import TeamCategoryResponse, TeamDistrictResponse
    
    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        created_at=team.created_at,
        updated_at=team.updated_at,
        categories=[
            TeamCategoryResponse(
                team_id=tc.team_id,
                category_id=tc.category_id,
                category_name=tc.category.name,
            )
            for tc in team.team_categories
        ],
        districts=[
            TeamDistrictResponse(
                team_id=td.team_id,
                district_id=td.district_id,
                district_name=td.district.name,
                city=td.district.city,
            )
            for td in team.team_districts
        ],
        members=[
            TeamMemberResponse(
                id=member.id,
                name=member.name,
                email=getattr(member, "email", None),
                phone_number=member.phone_number,
                role=member.role.value,
            )
            for member in team.members
            if member.deleted_at is None
        ],
    )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    db: DatabaseSession,
    _: ManagerUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TeamListResponse:
    """List teams with member count (only active members), paginated."""
    offset = (page - 1) * page_size

    # Total team count (not affected by joins)
    total_stmt = select(func.count(Team.id))
    total_result = await db.execute(total_stmt)
    total = int(total_result.scalar_one())

    # Page items with active member count
    stmt = (
        select(Team, func.count(User.id).label("member_count"))
        .outerjoin(User, (User.team_id == Team.id) & (User.deleted_at.is_(None)))
        .group_by(Team.id)
        .order_by(Team.name)
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = [
        TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=int(member_count or 0),
            active_ticket_count=0,  # TODO: Ticket join varsa ekleriz
        )
        for team, member_count in rows
    ]

    return TeamListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ✅ IMPORTANT: Must be BEFORE "/{team_id}" route to avoid path conflicts
@router.get("/unassigned/members", response_model=list[UnassignedMemberResponse])
async def list_unassigned_members(
    db: DatabaseSession,
    _: ManagerUser,
) -> list[UnassignedMemberResponse]:
    """List active users who are not assigned to any team."""
    stmt = (
        select(User)
        .where(
            User.deleted_at.is_(None),
            User.is_active.is_(True),
            User.team_id.is_(None),
        )
        .order_by(User.name)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        UnassignedMemberResponse(
            id=u.id,
            name=u.name,
            phone_number=u.phone_number,
            role=u.role.value,
        )
        for u in users
    ]


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: uuid.UUID,
    db: DatabaseSession,
    _: ManagerUser,
) -> TeamDetailResponse:
    """Get team details including members."""
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
    """Create a new team with categories and districts."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating team: {team_data.name}")
    logger.info(f"  Categories: {team_data.category_ids}")
    logger.info(f"  Districts: {team_data.district_ids}")
    
    existing = await db.execute(select(Team).where(Team.name == team_data.name))
    if existing.scalar_one_or_none():
        raise ConflictException(detail="Team with this name already exists")

    team = Team(
        name=team_data.name,
        description=team_data.description,
    )
    db.add(team)
    await db.flush()  # Get team.id before creating associations

    # Create TeamCategory associations
    for category_id in team_data.category_ids:
        team_category = TeamCategory(
            team_id=team.id,
            category_id=category_id,
        )
        db.add(team_category)
        logger.info(f"  Added category {category_id} to team")

    # Create TeamDistrict associations
    for district_id in team_data.district_ids:
        team_district = TeamDistrict(
            team_id=team.id,
            district_id=district_id,
        )
        db.add(team_district)
        logger.info(f"  Added district {district_id} to team")

    await db.commit()
    await db.refresh(team)
    logger.info(f"Team {team.name} created successfully with {len(team_data.category_ids)} categories and {len(team_data.district_ids)} districts")
    return TeamResponse.model_validate(team)


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: uuid.UUID,
    team_data: TeamUpdate,
    db: DatabaseSession,
    _: ManagerUser,
) -> TeamResponse:
    """Update a team."""
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

    Members will have team_id set to NULL before deleting the team.
    """
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

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
    """Add (or move) a user into a team."""
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    user_check = await db.execute(
        select(User.id, User.team_id)
        .where(User.id == user_id, User.deleted_at.is_(None))
    )
    row = user_check.first()
    if not row:
        raise NotFoundException(detail="User not found")

    current_team_id = row.team_id

    if current_team_id == team_id:
        team_full = await _get_team_with_members(db, team_id)
        return _to_team_detail_response(team_full)  # type: ignore[arg-type]

    res = await db.execute(
        update(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .values(team_id=team_id)
    )
    if res.rowcount == 0:
        raise NotFoundException(detail="User not found")

    await db.commit()

    team_full = await _get_team_with_members(db, team_id)
    return _to_team_detail_response(team_full)  # type: ignore[arg-type]


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: DatabaseSession,
    _: ManagerUser,
) -> None:
    """Remove a user from a team (sets team_id = NULL)."""
    team = await db.get(Team, team_id)
    if not team:
        raise NotFoundException(detail="Team not found")

    res = await db.execute(
        update(User)
        .where(
            User.id == user_id,
            User.deleted_at.is_(None),
            User.team_id == team_id,
        )
        .values(team_id=None)
    )

    if res.rowcount == 0:
        exists = await db.execute(
            select(User.id).where(User.id == user_id, User.deleted_at.is_(None))
        )
        if not exists.scalar_one_or_none():
            raise NotFoundException(detail="User not found")
        raise NotFoundException(detail="User is not a member of this team")

    await db.commit()
