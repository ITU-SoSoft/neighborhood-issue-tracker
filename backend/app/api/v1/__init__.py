"""API v1 package initialization."""
from fastapi import APIRouter

from app.api.v1 import teams  # <-- ekle

api_router = APIRouter()

api_router.include_router(teams.router, prefix="/teams", tags=["teams"])  # <-- ekle
