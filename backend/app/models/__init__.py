"""SQLAlchemy models package."""

from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.address import SavedAddress
from app.models.category import Category
from app.models.comment import Comment
from app.models.district import District
from app.models.escalation import EscalationRequest, EscalationStatus
from app.models.feedback import Feedback
from app.models.photo import Photo, PhotoType
from app.models.team import Team, TeamCategory, TeamDistrict
from app.models.notification import Notification, NotificationType
from app.models.ticket import Location, StatusLog, Ticket, TicketFollower, TicketStatus
from app.models.user import EmailVerificationToken, OTPCode, User, UserRole

__all__ = [
    # Base mixins
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # Models
    "User",
    "UserRole",
    "OTPCode",
    "EmailVerificationToken",
    "SavedAddress",
    "Team",
    "TeamCategory",
    "TeamDistrict",
    "District",
    "Category",
    "Location",
    "Ticket",
    "TicketStatus",
    "TicketFollower",
    "StatusLog",
    "Photo",
    "PhotoType",
    "Comment",
    "Feedback",
    "EscalationRequest",
    "EscalationStatus",
    "Notification",
    "NotificationType",
]
