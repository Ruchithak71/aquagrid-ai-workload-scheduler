"""Health check endpoint."""

from fastapi import APIRouter
from src.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return health status of the AquaGrid API service."""
    return HealthResponse()
