"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.config import settings
from app.database import create_tables, engine
from app.scripts.seed import seed_categories, seed_users
from app.scripts.seed_teams import seed_teams

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Sets up resources on startup and cleans up on shutdown.
    """
    # Startup: Try to create tables and seed data if in development mode
    if settings.debug:
        try:
            await create_tables()
            logger.info("Database tables created/verified")
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
            logger.warning(f"Could not create tables (DB may not be available): {e}")

    yield

    # Shutdown: Dispose engine
    try:
        await engine.dispose()
    except Exception:
        pass


def add_cors_headers(
    response: JSONResponse, request: Request | None = None
) -> JSONResponse:
    """Add CORS headers to error responses."""
    # Get origin from request or use first allowed origin
    origin = "*"
    if request and "origin" in request.headers:
        request_origin = request.headers["origin"]
        if request_origin in settings.cors_origins_list:
            origin = request_origin
    elif settings.cors_origins_list:
        origin = settings.cors_origins_list[0]

    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Vary"] = "Origin"
    return response


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions with CORS headers."""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
    return add_cors_headers(response, request)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with CORS headers."""
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = dict(error)
        # Convert ValueError objects in ctx to strings
        if "ctx" in error_dict and "error" in error_dict["ctx"]:
            error_dict["ctx"]["error"] = str(error_dict["ctx"]["error"])
        errors.append(error_dict)
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )
    return add_cors_headers(response, request)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with CORS headers."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
    return add_cors_headers(response, request)


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
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

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
