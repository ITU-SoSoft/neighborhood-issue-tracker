"""Escalation schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.escalation import EscalationStatus
from app.schemas.base import BaseSchema


class EscalationCreate(BaseSchema):
    """Schema for creating an escalation request."""

    ticket_id: UUID
    reason: str = Field(..., min_length=10, max_length=2000)


class EscalationReview(BaseSchema):
    """Schema for reviewing (approving/rejecting) an escalation."""

    comment: str | None = Field(default=None, max_length=1000)


class EscalationResponse(BaseSchema):
    """Escalation response schema."""

    id: UUID
    ticket_id: UUID
    ticket_title: str | None = None
    requester_id: UUID | None
    requester_name: str | None = None
    reviewer_id: UUID | None
    reviewer_name: str | None = None
    reason: str
    status: EscalationStatus
    review_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None


class EscalationListResponse(BaseSchema):
    """Response for listing escalations."""

    items: list[EscalationResponse]
    total: int
