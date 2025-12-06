"""Saved addresses API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, get_current_user
from app.models import SavedAddress, User
from app.schemas.address import (
    SavedAddressCreate,
    SavedAddressListResponse,
    SavedAddressResponse,
    SavedAddressUpdate,
)

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=SavedAddressListResponse)
async def get_saved_addresses(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SavedAddressListResponse:
    """Get all saved addresses for the current user."""
    # Get count
    count_query = select(func.count()).select_from(SavedAddress).where(
        SavedAddress.user_id == current_user.id
    )
    total = await session.scalar(count_query) or 0

    # Get addresses
    query = (
        select(SavedAddress)
        .where(SavedAddress.user_id == current_user.id)
        .order_by(SavedAddress.created_at.desc())
    )
    result = await session.execute(query)
    addresses = result.scalars().all()

    return SavedAddressListResponse(
        items=[SavedAddressResponse.model_validate(addr) for addr in addresses],
        total=total,
    )


@router.post("", response_model=SavedAddressResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_address(
    data: SavedAddressCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SavedAddressResponse:
    """Create a new saved address for the current user."""
    # Check if user already has an address with this name
    existing_query = select(SavedAddress).where(
        SavedAddress.user_id == current_user.id,
        SavedAddress.name == data.name,
    )
    existing = await session.scalar(existing_query)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An address with name '{data.name}' already exists",
        )

    # Limit to 10 addresses per user
    count_query = select(func.count()).select_from(SavedAddress).where(
        SavedAddress.user_id == current_user.id
    )
    count = await session.scalar(count_query) or 0
    if count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum number of saved addresses (10) reached",
        )

    address = SavedAddress(
        user_id=current_user.id,
        name=data.name,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        city=data.city,
    )
    session.add(address)
    await session.commit()
    await session.refresh(address)

    return SavedAddressResponse.model_validate(address)


@router.get("/{address_id}", response_model=SavedAddressResponse)
async def get_saved_address(
    address_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SavedAddressResponse:
    """Get a specific saved address."""
    query = select(SavedAddress).where(
        SavedAddress.id == address_id,
        SavedAddress.user_id == current_user.id,
    )
    address = await session.scalar(query)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    return SavedAddressResponse.model_validate(address)


@router.put("/{address_id}", response_model=SavedAddressResponse)
async def update_saved_address(
    address_id: UUID,
    data: SavedAddressUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> SavedAddressResponse:
    """Update a saved address."""
    query = select(SavedAddress).where(
        SavedAddress.id == address_id,
        SavedAddress.user_id == current_user.id,
    )
    address = await session.scalar(query)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    # Check for duplicate name if name is being changed
    if data.name and data.name != address.name:
        existing_query = select(SavedAddress).where(
            SavedAddress.user_id == current_user.id,
            SavedAddress.name == data.name,
            SavedAddress.id != address_id,
        )
        existing = await session.scalar(existing_query)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An address with name '{data.name}' already exists",
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)

    await session.commit()
    await session.refresh(address)

    return SavedAddressResponse.model_validate(address)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_address(
    address_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete a saved address."""
    query = select(SavedAddress).where(
        SavedAddress.id == address_id,
        SavedAddress.user_id == current_user.id,
    )
    address = await session.scalar(query)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    await session.delete(address)
    await session.commit()

