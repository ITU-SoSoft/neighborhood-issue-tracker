"""Unit tests for addresses API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.addresses import (
    get_saved_addresses,
    create_saved_address,
    get_saved_address,
    update_saved_address,
    delete_saved_address,
)
from app.models.address import SavedAddress
from app.models.user import User, UserRole
from app.schemas.address import SavedAddressCreate, SavedAddressUpdate


class TestGetSavedAddresses:
    """Tests for get_saved_addresses endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        return session

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )

    async def test_get_saved_addresses_success(self, mock_session, citizen_user):
        """Should return list of saved addresses."""
        now = datetime.now(timezone.utc)
        address = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="Home",
            address="123 Main St",
            latitude=41.0082,
            longitude=28.9784,
            city="Istanbul",
            created_at=now,
            updated_at=now,
        )

        # Mock count query
        mock_session.scalar.return_value = 1

        # Mock addresses query
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [address]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await get_saved_addresses(citizen_user, mock_session)

        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].name == "Home"

    async def test_get_saved_addresses_empty(self, mock_session, citizen_user):
        """Should return empty list when no addresses."""
        mock_session.scalar.return_value = 0

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await get_saved_addresses(citizen_user, mock_session)

        assert result.total == 0
        assert len(result.items) == 0


class TestCreateSavedAddress:
    """Tests for create_saved_address endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_create_saved_address_success(self, mock_session, citizen_user):
        """Should create a new saved address."""
        data = SavedAddressCreate(
            name="Home",
            address="123 Main St",
            latitude=41.0082,
            longitude=28.9784,
            city="Istanbul",
        )

        # Mock: no existing address with this name
        mock_session.scalar.side_effect = [None, 0]  # No existing, count = 0

        async def mock_refresh(addr):
            addr.id = uuid.uuid4()
            addr.created_at = datetime.now(timezone.utc)
            addr.updated_at = datetime.now(timezone.utc)

        mock_session.refresh = mock_refresh

        result = await create_saved_address(data, citizen_user, mock_session)

        assert result.name == "Home"
        assert result.address == "123 Main St"
        mock_session.add.assert_called_once()

    async def test_create_saved_address_duplicate_name(
        self, mock_session, citizen_user
    ):
        """Should raise HTTPException for duplicate name."""
        data = SavedAddressCreate(
            name="Home",
            address="123 Main St",
            latitude=41.0082,
            longitude=28.9784,
            city="Istanbul",
        )

        # Mock: existing address with this name
        existing = SavedAddress(id=uuid.uuid4(), name="Home")
        mock_session.scalar.return_value = existing

        with pytest.raises(HTTPException) as exc_info:
            await create_saved_address(data, citizen_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    async def test_create_saved_address_max_limit(self, mock_session, citizen_user):
        """Should raise HTTPException when max addresses reached."""
        data = SavedAddressCreate(
            name="Work",
            address="456 Office Blvd",
            latitude=41.0082,
            longitude=28.9784,
            city="Istanbul",
        )

        # Mock: no duplicate, but at max count
        mock_session.scalar.side_effect = [None, 10]  # No existing, count = 10

        with pytest.raises(HTTPException) as exc_info:
            await create_saved_address(data, citizen_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "Maximum" in str(exc_info.value.detail)


class TestGetSavedAddress:
    """Tests for get_saved_address endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.scalar = AsyncMock()
        return session

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_get_saved_address_success(self, mock_session, citizen_user):
        """Should return a saved address."""
        address_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        address = SavedAddress(
            id=address_id,
            user_id=citizen_user.id,
            name="Home",
            address="123 Main St",
            latitude=41.0082,
            longitude=28.9784,
            city="Istanbul",
            created_at=now,
            updated_at=now,
        )

        mock_session.scalar.return_value = address

        result = await get_saved_address(address_id, citizen_user, mock_session)

        assert result.id == address_id
        assert result.name == "Home"

    async def test_get_saved_address_not_found(self, mock_session, citizen_user):
        """Should raise HTTPException when address not found."""
        address_id = uuid.uuid4()
        mock_session.scalar.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_saved_address(address_id, citizen_user, mock_session)

        assert exc_info.value.status_code == 404


class TestUpdateSavedAddress:
    """Tests for update_saved_address endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.scalar = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_update_saved_address_success(self, mock_session, citizen_user):
        """Should update a saved address."""
        address_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        address = SavedAddress(
            id=address_id,
            user_id=citizen_user.id,
            name="Home",
            address="123 Main St",
            latitude=41.0082,
            longitude=28.9784,
            city="Istanbul",
            created_at=now,
            updated_at=now,
        )

        # First call returns the address, second call returns None (no duplicate)
        mock_session.scalar.side_effect = [address, None]

        data = SavedAddressUpdate(name="New Home")

        result = await update_saved_address(
            address_id, data, citizen_user, mock_session
        )

        assert result.name == "New Home"

    async def test_update_saved_address_not_found(self, mock_session, citizen_user):
        """Should raise HTTPException when address not found."""
        address_id = uuid.uuid4()
        mock_session.scalar.return_value = None

        data = SavedAddressUpdate(name="New Home")

        with pytest.raises(HTTPException) as exc_info:
            await update_saved_address(address_id, data, citizen_user, mock_session)

        assert exc_info.value.status_code == 404


class TestDeleteSavedAddress:
    """Tests for delete_saved_address endpoint."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.scalar = AsyncMock()
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_delete_saved_address_success(self, mock_session, citizen_user):
        """Should delete a saved address."""
        address_id = uuid.uuid4()
        address = SavedAddress(
            id=address_id,
            user_id=citizen_user.id,
            name="Home",
        )

        mock_session.scalar.return_value = address

        await delete_saved_address(address_id, citizen_user, mock_session)

        mock_session.delete.assert_called_once_with(address)
        mock_session.commit.assert_called_once()

    async def test_delete_saved_address_not_found(self, mock_session, citizen_user):
        """Should raise HTTPException when address not found."""
        address_id = uuid.uuid4()
        mock_session.scalar.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await delete_saved_address(address_id, citizen_user, mock_session)

        assert exc_info.value.status_code == 404
