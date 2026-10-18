"""Environmental conditions and weather profiles."""

from pydantic import BaseModel, Field, model_validator


class HourlyEnvironmentalCondition(BaseModel):
    """Environmental parameters for a specific site at a single hour."""

    hour: int = Field(..., ge=0, le=23, description="Hour index (0-23)")
    temperature_c: float = Field(
        ...,
        description="Ambient dry-bulb temperature in degrees Celsius",
    )
    carbon_intensity_g_per_kwh: float = Field(
        ...,
        ge=0.0,
        description="Grid carbon intensity in grams CO2eq per kilowatt-hour",
    )
    electricity_price_per_kwh: float = Field(
        ...,
        ge=0.0,
        description="Wholesale electricity price in dollars per kilowatt-hour",
    )
    grid_water_intensity_l_per_kwh: float = Field(
        default=1.5,
        ge=0.0,
        description="Energy-Water Intensity Factor (EWIF): Litres consumed per kWh generated",
    )


class SiteEnvironmentalProfile(BaseModel):
    """Complete 24-hour environmental profile for a given data centre site."""

    site_id: str = Field(..., description="ID of the matching data centre site")
    hourly_conditions: list[HourlyEnvironmentalCondition] = Field(
        ...,
        description="Ordered list of hourly conditions for 24 hours",
    )

    @model_validator(mode="after")
    def validate_24_hours(self) -> "SiteEnvironmentalProfile":
        """Verify that exactly 24 consecutive hours (0 through 23) are provided."""
        if len(self.hourly_conditions) != 24:
            raise ValueError(
                f"Environmental profile must have exactly 24 hours, got {len(self.hourly_conditions)}."
            )
        hours = [cond.hour for cond in self.hourly_conditions]
        expected = list(range(24))
        if hours != expected:
            raise ValueError(
                f"Hourly conditions must cover hours 0..23 in order, got: {hours}."
            )
        return self

    def get_hour(self, hour: int) -> HourlyEnvironmentalCondition:
        """Lookup condition for a specific hour index."""
        if not (0 <= hour <= 23):
            raise IndexError(f"Hour {hour} out of bounds (0-23)")
        return self.hourly_conditions[hour]
