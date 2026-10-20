"""Data Centre Site schema and validation."""

from enum import Enum
from pydantic import BaseModel, Field


class CoolingTechnology(str, Enum):
    """Cooling mechanism employed by a data centre."""
    EVAPORATIVE = "evaporative"
    DRY_COOLING = "dry_cooling"
    DIRECT_TO_CHIP = "direct_to_chip"


class DatacenterSite(BaseModel):
    """Represents a physical data centre site and its operational constraints."""

    id: str = Field(..., description="Unique slug for the facility (e.g. 'phoenix-01')")
    name: str = Field(..., description="Human-readable facility name")
    location: str = Field(..., description="Geographical location, e.g. 'Phoenix, AZ'")
    gpu_capacity: int = Field(
        ...,
        gt=0,
        description="Total concurrent GPUs physically available (must be > 0)",
    )
    cooling_type: CoolingTechnology = Field(
        default=CoolingTechnology.EVAPORATIVE,
        description="Cooling architecture used on-site",
    )
    base_pue: float = Field(
        default=1.15,
        ge=1.0,
        description="Baseline Power Usage Effectiveness (>= 1.0)",
    )
    pue_temp_slope: float = Field(
        default=0.01,
        ge=0.0,
        description="Rate of PUE increase per °C above economizer threshold",
    )
    base_wue: float = Field(
        default=0.2,
        ge=0.0,
        description="Baseline direct Water Usage Effectiveness (L/kWh) under free cooling",
    )
    economizer_temp_c: float = Field(
        default=18.0,
        description="Ambient dry-bulb temperature (°C) above which active water cooling starts",
    )
    wue_temp_slope: float = Field(
        default=0.08,
        ge=0.0,
        description="Rate of direct WUE increase per °C above economizer threshold (L/kWh/°C)",
    )
    daily_water_budget_liters: float = Field(
        ...,
        ge=0.0,
        description="Maximum allowed direct water consumption over the 24-hour horizon",
    )
    gpu_power_kw: float = Field(
        default=0.7,
        gt=0.0,
        description="Thermal Design Power (TDP) per GPU in kilowatts under load",
    )
