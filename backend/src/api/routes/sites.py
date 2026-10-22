"""Datacenter sites and environmental profiles routes."""

from fastapi import APIRouter, HTTPException

from src.models import DatacenterSite, SiteEnvironmentalProfile
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
)

router = APIRouter(prefix="/sites", tags=["Sites & Environmental"])


@router.get("", response_model=list[DatacenterSite])
def list_sites() -> list[DatacenterSite]:
    """Retrieve all available datacenter facilities."""
    return get_default_sites()


@router.get("/{site_id}/environmental", response_model=SiteEnvironmentalProfile)
def get_site_environmental_profile(site_id: str) -> SiteEnvironmentalProfile:
    """Retrieve 24-hour environmental telemetry (temperature, carbon, price) for a site."""
    profiles = get_default_environmental_profiles()
    profile = profiles.get(site_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Environmental profile for site '{site_id}' not found.",
        )
    return profile
