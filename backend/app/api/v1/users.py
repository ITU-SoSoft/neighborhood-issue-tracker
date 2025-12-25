"""User management API routes."""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DatabaseSession, ManagerUser
from app.config import settings
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    UserNotFoundException,
)
from app.core.security import hash_password, verify_password
from app.models.user import EmailVerificationToken, User, UserRole
from app.schemas.user import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)
from app.services.email import email_service

router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    request: UserCreateRequest,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> UserResponse:
    """Create a new staff user (manager only).

    Creates a support staff or manager user. An invite email will be sent
    to the user's email address with a link to set their password.

    The user must verify their phone number when setting their password
    as a security measure.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"Creating user: {request.email}, phone: {request.phone_number}, role: {request.role}"
    )

    # Check if email already exists
    existing_email = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    if existing_email.scalar_one_or_none():
        raise BadRequestException(detail="Email is already registered")

    # Check if phone number already exists
    existing_phone = await db.execute(
        select(User).where(
            User.phone_number == request.phone_number, User.deleted_at.is_(None)
        )
    )
    if existing_phone.scalar_one_or_none():
        raise BadRequestException(detail="Phone number is already registered")

    # Create user without password (will be set via invite flow)
    new_user = User(
        name=request.name,
        email=request.email,
        phone_number=request.phone_number,
        password_hash="",  # Will be set when user accepts invite
        role=request.role,
        team_id=request.team_id,
        is_verified=False,  # Will be verified when user sets password
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate invite token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.email_verification_expire_hours
    )

    invite_token = EmailVerificationToken(
        user_id=new_user.id,
        token=token,
        token_type="invite",
        expires_at=expires_at,
    )
    db.add(invite_token)
    await db.commit()

    # Send invite email
    await email_service.send_staff_invite_email(
        to_email=new_user.email,
        user_name=new_user.name,
        role=new_user.role.value,
        token=token,
    )

    return UserResponse.model_validate(new_user)


@router.get(
    "/",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_users(
    current_user: ManagerUser,
    db: DatabaseSession,
    role: str | None = Query(default=None),
    team_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
) -> UserListResponse:
    """List all users (manager only).

    Supports filtering by role and team.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"Listing users: role={role}, team_id={team_id}, page={page}, page_size={page_size}"
    )

    # Build query
    query = select(User).where(User.deleted_at.is_(None))

    if role:
        try:
            role_enum = UserRole(role)
            query = query.where(User.role == role_enum)
        except ValueError:
            from app.core.exceptions import BadRequestException

            raise BadRequestException(detail=f"Invalid role: {role}")
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
    Password can be updated by providing current_password and new_password.
    """
    if current_user.id != user_id:
        raise ForbiddenException(detail="Cannot update other users' profiles")

    # Update password if provided
    if request.new_password is not None:
        if request.current_password is None:
            raise BadRequestException(
                detail="Current password is required to change password"
            )
        # Verify current password
        if not verify_password(request.current_password, current_user.password_hash):
            raise BadRequestException(detail="Current password is incorrect")
        # Hash and set new password
        current_user.password_hash = hash_password(request.new_password)

    # Update fields
    if request.name is not None:
        current_user.name = request.name
    if request.email is not None:
        current_user.email = request.email
    if request.phone_number is not None:
        # Check if phone number is already taken by another user
        existing = await db.execute(
            select(User).where(
                User.phone_number == request.phone_number,
                User.id != current_user.id,
                User.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise BadRequestException(detail="Phone number is already in use")
        current_user.phone_number = request.phone_number

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
