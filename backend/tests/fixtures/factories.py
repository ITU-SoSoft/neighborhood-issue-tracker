"""Factory Boy factories for generating test data."""

import factory
import factory.fuzzy
from datetime import datetime, timezone
import uuid
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketStatus, Location
from app.models.category import Category
from app.models.team import Team
from app.models.comment import Comment
from app.models.feedback import Feedback
from app.models.notification import Notification, NotificationType

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    phone_number = factory.Sequence(lambda n: f"+90555{n:07d}")
    name = factory.Faker("name")
    email = factory.Faker("email")
    password_hash = "hashed_password_for_testing"
    role = UserRole.CITIZEN
    is_verified = True
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class CategoryFactory(factory.Factory):
    class Meta:
        model = Category

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Category {n}")
    description = factory.Faker("sentence")
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class TeamFactory(factory.Factory):
    class Meta:
        model = Team

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Team {n}")
    description = factory.Faker("sentence")
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class LocationFactory(factory.Factory):
    class Meta:
        model = Location

    id = factory.LazyFunction(uuid.uuid4)
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    address = factory.Faker("address")
    city = "Istanbul"
    district = "Beyoglu"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class TicketFactory(factory.Factory):
    class Meta:
        model = Ticket

    id = factory.LazyFunction(uuid.uuid4)
    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    status = TicketStatus.NEW
    reporter_id = factory.SubFactory(UserFactory)
    category_id = factory.SubFactory(CategoryFactory)
    location_id = factory.SubFactory(LocationFactory)
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class CommentFactory(factory.Factory):
    class Meta:
        model = Comment

    id = factory.LazyFunction(uuid.uuid4)
    content = factory.Faker("paragraph")
    user_id = factory.SubFactory(UserFactory)
    ticket_id = factory.SubFactory(TicketFactory)
    is_internal = False
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class FeedbackFactory(factory.Factory):
    class Meta:
        model = Feedback

    id = factory.LazyFunction(uuid.uuid4)
    rating = factory.fuzzy.FuzzyInteger(1, 5)
    comment = factory.Faker("sentence")
    user_id = factory.SubFactory(UserFactory)
    ticket_id = factory.SubFactory(TicketFactory)
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))

class NotificationFactory(factory.Factory):
    class Meta:
        model = Notification

    id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.SubFactory(UserFactory)
    notification_type = NotificationType.TICKET_CREATED
    title = factory.Faker("sentence", nb_words=3)
    message = factory.Faker("sentence")
    is_read = False
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
