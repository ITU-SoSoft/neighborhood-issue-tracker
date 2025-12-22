"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.database import engine
from app.scripts.seed import seed_categories, seed_users
from app.scripts.seed_teams import seed_teams

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Sets up resources on startup and cleans up on shutdown.
    """
    # Startup: Seed data if in development mode
    # NOTE: Tables should be created via Alembic migrations first
    # Run: docker exec sosoft-backend uv run alembic upgrade head
    if settings.debug:
        try:
            # Seed default categories
            await seed_categories()
            logger.info("Default categories seeded")
            # Seed default users
            await seed_users()
            logger.info("Default users seeded")
            # Seed teams
            await seed_teams()
            logger.info("Default teams seeded")
        except Exception as e:
            logger.warning(f"Could not seed data (DB may not be ready): {e}")

    yield

    # Shutdown: Dispose engine
    try:
        await engine.dispose()
    except Exception:
        pass


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="SoSoft - Neighborhood Issue Reporting & Tracking Platform API",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
        redirect_slashes=False,  # Disable automatic trailing slash redirects
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


# Create app instance
app = create_application()


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "name": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
