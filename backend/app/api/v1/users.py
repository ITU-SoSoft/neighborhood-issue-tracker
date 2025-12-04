"""User management API routes."""

from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DatabaseSession, ManagerUser
from app.core.exceptions import ForbiddenException, UserNotFoundException
from app.models.user import User, UserRole
from app.schemas.user import (
    UserListResponse,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)

router = APIRouter()


@router.get(
    "/",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_users(
    current_user: ManagerUser,
    db: DatabaseSession,
    role: UserRole | None = None,
    team_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> UserListResponse:
    """List all users (manager only).

    Supports filtering by role and team.
    """
    # Build query
    query = select(User).where(User.deleted_at.is_(None))

    if role:
        query = query.where(User.role == role)
    if team_id:
        query = query.where(User.team_id == team_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> UserResponse:
    """Get a user by ID.

    Users can view their own profile.
    Managers can view any user's profile.
    """
    # Check permissions
    if current_user.id != user_id and current_user.role != UserRole.MANAGER:
        raise ForbiddenException(detail="Cannot view other users' profiles")

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundException()

    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: UUID,
    request: UserUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> UserResponse:
    """Update a user's profile.

    Users can only update their own profile.
    """
    if current_user.id != user_id:
        raise ForbiddenException(detail="Cannot update other users' profiles")

    # Update fields
    if request.name is not None:
        current_user.name = request.name
    if request.email is not None:
        current_user.email = request.email

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user_role(
    user_id: UUID,
    request: UserRoleUpdate,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> UserResponse:
    """Update a user's role (manager only).

    Used to promote citizens to support members or managers.
    """
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundException()

    # Update role and team
    user.role = request.role
    if request.team_id is not None:
        user.team_id = request.team_id

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: UUID,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> None:
    """Soft delete a user (manager only)."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundException()

    # Soft delete
    from datetime import datetime, timezone

    user.deleted_at = datetime.now(timezone.utc)

    await db.commit()
