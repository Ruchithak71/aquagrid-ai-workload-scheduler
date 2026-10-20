"""Physical resource and environmental impact calculator for AquaGrid."""

from src.models import (
    DatacenterSite,
    HourlyEnvironmentalCondition,
    HourlyExecution,
)


def calculate_hourly_pue(site: DatacenterSite, ambient_temp_c: float) -> float:
    """Calculate site Power Usage Effectiveness based on ambient temperature.

    Formula:
        PUE(T) = base_pue + pue_temp_slope * max(0, T - economizer_temp_c)
    """
    if ambient_temp_c <= site.economizer_temp_c:
        return site.base_pue
    return site.base_pue + site.pue_temp_slope * (ambient_temp_c - site.economizer_temp_c)


def calculate_hourly_wue(site: DatacenterSite, ambient_temp_c: float) -> float:
    """Calculate direct Water Usage Effectiveness (L/kWh) based on ambient temperature.

    Formula:
        WUE_direct(T) = base_wue + wue_temp_slope * max(0, T - economizer_temp_c)
    """
    if ambient_temp_c <= site.economizer_temp_c:
        return site.base_wue
    return site.base_wue + site.wue_temp_slope * (ambient_temp_c - site.economizer_temp_c)


def calculate_indirect_water(
    total_energy_kwh: float,
    grid_water_intensity_l_per_kwh: float,
) -> float:
    """Calculate off-site power generation water consumption (Litres).

    Formula:
        W_indirect = E_total * EWIF_grid
    """
    return total_energy_kwh * grid_water_intensity_l_per_kwh


def calculate_carbon_emissions(
    total_energy_kwh: float,
    carbon_intensity_g_per_kwh: float,
) -> float:
    """Calculate operational carbon emissions in kilograms of CO2eq.

    Formula:
        Carbon = E_total * CI_grid * 10^-3  (kg CO2eq)
    """
    return total_energy_kwh * carbon_intensity_g_per_kwh * 1e-3


def calculate_electricity_cost(
    total_energy_kwh: float,
    electricity_price_per_kwh: float,
) -> float:
    """Calculate financial electricity cost in USD ($).

    Formula:
        Cost = E_total * Price_grid
    """
    return total_energy_kwh * electricity_price_per_kwh


def calculate_hourly_execution(
    site: DatacenterSite,
    workload_id: str,
    gpus_used: int,
    hour: int,
    condition: HourlyEnvironmentalCondition,
) -> HourlyExecution:
    """Compute the complete physical resource footprint for a 1-hour job execution slice.

    Args:
        site: The data-centre site where the job runs.
        workload_id: The ID of the running workload.
        gpus_used: Number of GPUs occupied during this hour.
        hour: The current simulation hour index (0-23).
        condition: Environmental conditions at this site and hour.

    Returns:
        HourlyExecution populated with IT energy, facility energy, direct/indirect water,
        carbon, and operational cost.
    """
    if gpus_used < 0:
        raise ValueError(f"gpus_used cannot be negative, got {gpus_used}")

    # 1. IT Energy (kWh for 1 hour duration)
    it_energy_kwh = gpus_used * site.gpu_power_kw * 1.0

    # 2. Total Facility Energy (accounting for temperature-dependent PUE)
    pue = calculate_hourly_pue(site, condition.temperature_c)
    total_energy_kwh = it_energy_kwh * pue

    # 3. Direct Cooling Water (evaporated on-site, Litres)
    wue_direct = calculate_hourly_wue(site, condition.temperature_c)
    direct_water_liters = it_energy_kwh * wue_direct

    # 4. Indirect Power Plant Water (Litres)
    indirect_water_liters = calculate_indirect_water(
        total_energy_kwh, condition.grid_water_intensity_l_per_kwh
    )

    # 5. Operational Carbon (kg CO2eq)
    carbon_kg = calculate_carbon_emissions(
        total_energy_kwh, condition.carbon_intensity_g_per_kwh
    )

    # 6. Financial Electricity Cost ($)
    cost_usd = calculate_electricity_cost(
        total_energy_kwh, condition.electricity_price_per_kwh
    )

    return HourlyExecution(
        workload_id=workload_id,
        site_id=site.id,
        hour=hour,
        gpus_used=gpus_used,
        it_energy_kwh=round(it_energy_kwh, 4),
        total_energy_kwh=round(total_energy_kwh, 4),
        direct_water_liters=round(direct_water_liters, 4),
        indirect_water_liters=round(indirect_water_liters, 4),
        carbon_kg=round(carbon_kg, 4),
        cost_usd=round(cost_usd, 4),
    )
