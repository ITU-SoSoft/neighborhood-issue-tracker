"""Analytics schemas."""

from uuid import UUID


from app.schemas.base import BaseSchema


class DashboardKPIs(BaseSchema):
    """Dashboard key performance indicators."""

    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    closed_tickets: int
    escalated_tickets: int
    resolution_rate: float  # Percentage
    average_rating: float | None
    average_resolution_hours: float | None


class HeatmapPoint(BaseSchema):
    """Single point on the heatmap."""

    latitude: float
    longitude: float
    count: int
    intensity: float  # 0.0 to 1.0


class HeatmapResponse(BaseSchema):
    """Heatmap data response."""

    points: list[HeatmapPoint]
    total_tickets: int
    max_count: int


class TeamPerformance(BaseSchema):
    """Team performance metrics."""

    team_id: UUID
    team_name: str
    total_assigned: int
    total_resolved: int
    open_tickets: int
    resolution_rate: float
    average_resolution_hours: float | None
    average_rating: float | None
    member_count: int


class TeamPerformanceResponse(BaseSchema):
    """Response for team performance."""

    items: list[TeamPerformance]


class MemberPerformance(BaseSchema):
    """Individual team member performance."""

    user_id: UUID
    user_name: str
    total_assigned: int
    total_resolved: int
    resolution_rate: float
    average_resolution_hours: float | None
    average_rating: float | None


class MemberPerformanceResponse(BaseSchema):
    """Response for member performance."""

    members: list[MemberPerformance]
    team_id: UUID
    team_name: str


class CategoryStats(BaseSchema):
    """Statistics by category."""

    category_id: UUID
    category_name: str
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    average_rating: float | None



class CategoryStatsResponse(BaseSchema):
    """Response for category statistics."""

    items: list[CategoryStats]


class NeighborhoodCategoryBreakdown(BaseSchema):
    """Category breakdown for a neighborhood."""

    category_name: str
    ticket_count: int


class NeighborhoodStats(BaseSchema):
    """Statistics for a single neighborhood."""

    district: str
    total_tickets: int
    category_breakdown: list[NeighborhoodCategoryBreakdown]


class NeighborhoodStatsResponse(BaseSchema):
    """Response for neighborhood statistics."""

    items: list[NeighborhoodStats]


class FeedbackTrend(BaseSchema):
    """Feedback trend data for a category."""

    category_id: UUID
    category_name: str
    total_feedbacks: int
    average_rating: float
    rating_distribution: dict[int, int]


class FeedbackTrendsResponse(BaseSchema):
    """Response for feedback trends."""

    items: list[FeedbackTrend]
