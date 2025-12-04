"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    categories,
    comments,
    escalations,
    feedback,
    teams,
    users,
)
from app.api.v1.tickets import router as tickets_router

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(tickets_router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(comments.router, prefix="/tickets", tags=["Comments"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
api_router.include_router(
    escalations.router, prefix="/escalations", tags=["Escalations"]
)
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
