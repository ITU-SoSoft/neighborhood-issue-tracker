"""Tickets API module - aggregates all ticket-related routers."""

from fastapi import APIRouter

from app.api.v1.tickets import assignments, crud, followers, photos, search, status

router = APIRouter()

# Include all sub-routers
# Order matters for path matching - static paths must come before dynamic ones!

# Static paths first
router.include_router(search.router)  # /nearby
router.include_router(assignments.router)  # /my, /assigned, /{id}/assign

# CRUD operations (includes /{ticket_id} paths)
router.include_router(crud.router)  # /, /{id}

# Sub-resource paths
router.include_router(status.router)  # /{id}/status
router.include_router(photos.router)  # /{id}/photos
router.include_router(followers.router)  # /{id}/follow
