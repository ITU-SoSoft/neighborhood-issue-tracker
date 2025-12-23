"""Integration tests for TeamAssignmentService - tests team matching with real database."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.district import District
from app.models.team import Team, TeamCategory, TeamDistrict
from app.models.ticket import Location, Ticket, TicketStatus
from app.models.user import User
from app.services.team_assignment_service import TeamAssignmentService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def district_kadikoy(db_session: AsyncSession) -> District:
    """Create Kadikoy district."""
    d = District(
        id=uuid.uuid4(),
        name="Kadikoy",
        city="Istanbul",
    )
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest.fixture
async def district_besiktas(db_session: AsyncSession) -> District:
    """Create Besiktas district."""
    d = District(
        id=uuid.uuid4(),
        name="Besiktas",
        city="Istanbul",
    )
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest.fixture
async def infrastructure_category(db_session: AsyncSession) -> Category:
    """Create infrastructure category."""
    cat = Category(
        id=uuid.uuid4(),
        name="Infrastructure",
        description="Road and building issues",
        is_active=True,
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


@pytest.fixture
async def lighting_category(db_session: AsyncSession) -> Category:
    """Create lighting category."""
    cat = Category(
        id=uuid.uuid4(),
        name="Lighting",
        description="Street lighting issues",
        is_active=True,
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


@pytest.fixture
async def team_kadikoy_infrastructure(
    db_session: AsyncSession,
    infrastructure_category: Category,
    district_kadikoy: District,
) -> Team:
    """Create a team that handles infrastructure in Kadikoy (Priority 1 match)."""
    team = Team(
        id=uuid.uuid4(),
        name="Kadikoy Infrastructure Team",
        description="Handles infrastructure in Kadikoy",
    )
    db_session.add(team)
    await db_session.flush()

    # Link team to category
    team_category = TeamCategory(
        team_id=team.id,
        category_id=infrastructure_category.id,
    )
    db_session.add(team_category)

    # Link team to district
    team_district = TeamDistrict(
        team_id=team.id,
        district_id=district_kadikoy.id,
    )
    db_session.add(team_district)

    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest.fixture
async def team_istanbul_lighting(
    db_session: AsyncSession,
    lighting_category: Category,
    district_besiktas: District,
) -> Team:
    """Create a team that handles lighting in any Istanbul district (Priority 2 match)."""
    team = Team(
        id=uuid.uuid4(),
        name="Istanbul Lighting Team",
        description="Handles lighting across Istanbul",
    )
    db_session.add(team)
    await db_session.flush()

    # Link team to category
    team_category = TeamCategory(
        team_id=team.id,
        category_id=lighting_category.id,
    )
    db_session.add(team_category)

    # Link team to a district in Istanbul (any district in city)
    team_district = TeamDistrict(
        team_id=team.id,
        district_id=district_besiktas.id,
    )
    db_session.add(team_district)

    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest.fixture
async def team_general_infrastructure(
    db_session: AsyncSession,
    infrastructure_category: Category,
) -> Team:
    """Create a team that handles infrastructure anywhere (Priority 3 match - no district)."""
    team = Team(
        id=uuid.uuid4(),
        name="General Infrastructure Team",
        description="Handles infrastructure anywhere",
    )
    db_session.add(team)
    await db_session.flush()

    # Link team to category only (no district)
    team_category = TeamCategory(
        team_id=team.id,
        category_id=infrastructure_category.id,
    )
    db_session.add(team_category)

    await db_session.commit()
    await db_session.refresh(team)
    return team


# ============================================================================
# Test: Find Matching Team - Priority Order
# ============================================================================


class TestFindMatchingTeam:
    """Tests for TeamAssignmentService.find_matching_team."""

    async def test_priority_1_category_and_district_match(
        self,
        db_session: AsyncSession,
        infrastructure_category: Category,
        district_kadikoy: District,
        team_kadikoy_infrastructure: Team,
        team_general_infrastructure: Team,  # Should NOT be selected
    ):
        """Should match team with both category AND district (Priority 1)."""
        service = TeamAssignmentService()

        result = await service.find_matching_team(
            session=db_session,
            category_id=infrastructure_category.id,
            district="Kadikoy",
            city="Istanbul",
        )

        assert result is not None
        assert result.id == team_kadikoy_infrastructure.id
        assert result.name == "Kadikoy Infrastructure Team"

    async def test_priority_2_category_and_city_match(
        self,
        db_session: AsyncSession,
        lighting_category: Category,
        district_besiktas: District,
        team_istanbul_lighting: Team,
    ):
        """Should match team with category in same city (Priority 2)."""
        service = TeamAssignmentService()

        # Request for Kadikoy, but team only has Besiktas
        # Should still match since both are in Istanbul
        result = await service.find_matching_team(
            session=db_session,
            category_id=lighting_category.id,
            district="Kadikoy",  # Different district
            city="Istanbul",
        )

        assert result is not None
        assert result.id == team_istanbul_lighting.id

    async def test_priority_3_category_only_match(
        self,
        db_session: AsyncSession,
        infrastructure_category: Category,
        team_general_infrastructure: Team,
    ):
        """Should match team with category only when no district match (Priority 3)."""
        service = TeamAssignmentService()

        # Request for a district/city with no specific team
        result = await service.find_matching_team(
            session=db_session,
            category_id=infrastructure_category.id,
            district="Uskudar",  # No team for this district
            city="Istanbul",
        )

        assert result is not None
        assert result.id == team_general_infrastructure.id

    async def test_no_match_returns_none(
        self,
        db_session: AsyncSession,
        lighting_category: Category,
    ):
        """Should return None when no team matches (manual assignment needed)."""
        service = TeamAssignmentService()

        # No team handles lighting (team_istanbul_lighting not created in this test)
        result = await service.find_matching_team(
            session=db_session,
            category_id=lighting_category.id,
            district="Kadikoy",
            city="Istanbul",
        )

        assert result is None

    async def test_match_without_district(
        self,
        db_session: AsyncSession,
        infrastructure_category: Category,
        team_general_infrastructure: Team,
    ):
        """Should find team when district is None."""
        service = TeamAssignmentService()

        result = await service.find_matching_team(
            session=db_session,
            category_id=infrastructure_category.id,
            district=None,  # No district specified
            city="Istanbul",
        )

        assert result is not None
        assert result.id == team_general_infrastructure.id


# ============================================================================
# Test: Get Team Workload
# ============================================================================


class TestGetTeamWorkload:
    """Tests for TeamAssignmentService.get_team_workload."""

    async def test_workload_counts_active_tickets(
        self,
        db_session: AsyncSession,
        team: Team,
        category: Category,
        citizen_user: User,
    ):
        """Should count NEW and IN_PROGRESS tickets."""
        service = TeamAssignmentService()

        # Create tickets with various statuses
        for i, status in enumerate(
            [
                TicketStatus.NEW,
                TicketStatus.NEW,
                TicketStatus.IN_PROGRESS,
                TicketStatus.RESOLVED,  # Should NOT count
                TicketStatus.CLOSED,  # Should NOT count
            ]
        ):
            location = Location(
                id=uuid.uuid4(),
                latitude=41.0082 + i * 0.001,
                longitude=28.9784,
                coordinates=f"POINT(28.9784 {41.0082 + i * 0.001})",
                address=f"Address {i}",
                city="Istanbul",
            )
            db_session.add(location)
            await db_session.flush()

            ticket = Ticket(
                id=uuid.uuid4(),
                title=f"Ticket {i}",
                description=f"Description {i}",
                status=status,
                category_id=category.id,
                location_id=location.id,
                reporter_id=citizen_user.id,
                team_id=team.id,
            )
            db_session.add(ticket)

        await db_session.commit()

        workload = await service.get_team_workload(db_session, team.id)

        # Should count 2 NEW + 1 IN_PROGRESS = 3
        assert workload == 3

    async def test_workload_excludes_deleted_tickets(
        self,
        db_session: AsyncSession,
        team: Team,
        category: Category,
        citizen_user: User,
    ):
        """Should not count soft-deleted tickets."""
        from datetime import datetime, timezone

        service = TeamAssignmentService()

        # Create a deleted ticket
        location = Location(
            id=uuid.uuid4(),
            latitude=41.0082,
            longitude=28.9784,
            coordinates="POINT(28.9784 41.0082)",
            address="Deleted Address",
            city="Istanbul",
        )
        db_session.add(location)
        await db_session.flush()

        ticket = Ticket(
            id=uuid.uuid4(),
            title="Deleted Ticket",
            description="This is deleted",
            status=TicketStatus.NEW,
            category_id=category.id,
            location_id=location.id,
            reporter_id=citizen_user.id,
            team_id=team.id,
            deleted_at=datetime.now(timezone.utc),  # Soft deleted
        )
        db_session.add(ticket)
        await db_session.commit()

        workload = await service.get_team_workload(db_session, team.id)

        assert workload == 0

    async def test_workload_for_team_with_no_tickets(
        self,
        db_session: AsyncSession,
        team: Team,
    ):
        """Should return 0 for team with no tickets."""
        service = TeamAssignmentService()

        workload = await service.get_team_workload(db_session, team.id)

        assert workload == 0

    async def test_workload_only_counts_team_tickets(
        self,
        db_session: AsyncSession,
        team: Team,
        other_team: Team,
        category: Category,
        citizen_user: User,
    ):
        """Should only count tickets assigned to the specific team."""
        service = TeamAssignmentService()

        # Create ticket for other team
        location = Location(
            id=uuid.uuid4(),
            latitude=41.0082,
            longitude=28.9784,
            coordinates="POINT(28.9784 41.0082)",
            address="Other Team Address",
            city="Istanbul",
        )
        db_session.add(location)
        await db_session.flush()

        ticket = Ticket(
            id=uuid.uuid4(),
            title="Other Team Ticket",
            description="Assigned to other team",
            status=TicketStatus.NEW,
            category_id=category.id,
            location_id=location.id,
            reporter_id=citizen_user.id,
            team_id=other_team.id,  # Different team
        )
        db_session.add(ticket)
        await db_session.commit()

        # Check workload for original team (should be 0)
        workload = await service.get_team_workload(db_session, team.id)

        assert workload == 0
