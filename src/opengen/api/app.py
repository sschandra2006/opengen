"""
Main FastAPI Application Factory for OpenGen.
Combines REST API, CORS middleware, lifespan events, and static dashboard serving.
"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from opengen.config import settings
from opengen.api.v1.routes import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure directories exist
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown logic if needed


def create_app() -> FastAPI:
    """Builds and configures the OpenGen FastAPI application."""
    app = FastAPI(
        title="OpenGen REST API",
        description="Self-hostable, multi-modal AI generation framework for documents, presentations, images, and handwriting.",
        version="1.0.0",
        lifespan=lifespan
    )

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API v1 routes
    app.include_router(v1_router)

    # Mount static assets for web UI if available
    legacy_static = Path("app/web/static")
    if legacy_static.exists():
        app.mount("/static", StaticFiles(directory=str(legacy_static)), name="static")

    return app


app = create_app()
