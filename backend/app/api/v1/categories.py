"""Category management API routes."""

from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import DatabaseSession, ManagerUser
from app.core.exceptions import CategoryNotFoundException, ConflictException
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=CategoryListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_categories(
    db: DatabaseSession,
    active_only: bool = True,
) -> CategoryListResponse:
    """List all categories.

    By default, only active categories are returned.
    """
    query = select(Category)
    if active_only:
        query = query.where(Category.is_active == True)  # noqa: E712

    result = await db.execute(query.order_by(Category.name))
    categories = result.scalars().all()

    return CategoryListResponse(
        items=[CategoryResponse.model_validate(c) for c in categories],
        total=len(categories),
    )


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_category(
    category_id: UUID,
    db: DatabaseSession,
) -> CategoryResponse:
    """Get a category by ID."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if category is None:
        raise CategoryNotFoundException()

    return CategoryResponse.model_validate(category)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    request: CategoryCreate,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> CategoryResponse:
    """Create a new category (manager only)."""
    # Check for duplicate name
    result = await db.execute(select(Category).where(Category.name == request.name))
    if result.scalar_one_or_none():
        raise ConflictException(detail="Category with this name already exists")

    category = Category(
        name=request.name,
        description=request.description,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return CategoryResponse.model_validate(category)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
async def update_category(
    category_id: UUID,
    request: CategoryUpdate,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> CategoryResponse:
    """Update a category (manager only)."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if category is None:
        raise CategoryNotFoundException()

    # Update fields
    if request.name is not None:
        # Check for duplicate name
        result = await db.execute(
            select(Category).where(
                Category.name == request.name,
                Category.id != category_id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException(detail="Category with this name already exists")
        category.name = request.name

    if request.description is not None:
        category.description = request.description
    if request.is_active is not None:
        category.is_active = request.is_active

    await db.commit()
    await db.refresh(category)

    return CategoryResponse.model_validate(category)
