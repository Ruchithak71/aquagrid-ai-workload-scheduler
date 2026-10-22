"""Main FastAPI application entrypoint for AquaGrid."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    health_router,
    sites_router,
    workloads_router,
    scheduling_router,
)


def create_app() -> FastAPI:
    """Application factory for AquaGrid backend."""
    app = FastAPI(
        title="AquaGrid: AI Workload Scheduler",
        description=(
            "Decision-support simulation and optimization platform for water, "
            "carbon, and energy-aware AI workload scheduling across distributed datacenters."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for local development and future React dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API route namespaces
    app.include_router(health_router, prefix="/api")
    app.include_router(sites_router, prefix="/api")
    app.include_router(workloads_router, prefix="/api")
    app.include_router(scheduling_router, prefix="/api")

    @app.get("/", tags=["Root"])
    def root():
        return {
            "message": "Welcome to AquaGrid AI Workload Scheduler API",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


app = create_app()
