"""Canonical benchmark datasets and synthetic scenarios for AquaGrid.

Provides realistic 24-hour summer weather, carbon intensity, wholesale electricity
prices, and EWIF vectors across three geographically distinct data-centre regions:
1. Phoenix, AZ (Desert, extreme heat, midday solar peak, strict water budget)
2. Quincy, WA (Pacific Northwest, cool climate, clean hydro, high grid EWIF)
3. Council Bluffs, IA (Midwest, moderate climate, nighttime wind power)
"""

from src.models import (
    DatacenterSite,
    CoolingTechnology,
    HourlyEnvironmentalCondition,
    SiteEnvironmentalProfile,
    Workload,
)


def get_default_sites() -> list[DatacenterSite]:
    """Return the three canonical data-centre facilities."""
    return [
        DatacenterSite(
            id="phoenix-01",
            name="Phoenix Desert Ridge Supercluster",
            location="Phoenix, AZ",
            gpu_capacity=128,
            cooling_type=CoolingTechnology.EVAPORATIVE,
            base_pue=1.15,
            pue_temp_slope=0.01,
            base_wue=0.20,
            economizer_temp_c=18.0,
            wue_temp_slope=0.08,
            daily_water_budget_liters=2500.0,  # Strict water cap (desert drought)
            gpu_power_kw=0.7,
        ),
        DatacenterSite(
            id="quincy-01",
            name="Quincy Columbia Basin Data Center",
            location="Quincy, WA",
            gpu_capacity=96,
            cooling_type=CoolingTechnology.DIRECT_TO_CHIP,
            base_pue=1.12,
            pue_temp_slope=0.008,
            base_wue=0.15,
            economizer_temp_c=16.0,
            wue_temp_slope=0.05,
            daily_water_budget_liters=4500.0,  # Generous water budget
            gpu_power_kw=0.7,
        ),
        DatacenterSite(
            id="council-bluffs-01",
            name="Council Bluffs Prairie Cluster",
            location="Council Bluffs, IA",
            gpu_capacity=128,
            cooling_type=CoolingTechnology.EVAPORATIVE,
            base_pue=1.18,
            pue_temp_slope=0.012,
            base_wue=0.25,
            economizer_temp_c=18.0,
            wue_temp_slope=0.07,
            daily_water_budget_liters=3500.0,  # Moderate water cap
            gpu_power_kw=0.7,
        ),
    ]


def get_default_environmental_profiles() -> dict[str, SiteEnvironmentalProfile]:
    """Return realistic 24-hour summer weather, carbon, and pricing profiles."""

    # 1. Phoenix, AZ: Summer desert heat curve, solar noon carbon drop
    phoenix_temps = [
        28.0, 27.0, 26.5, 26.0, 26.0, 27.5,
        30.0, 33.0, 36.0, 38.5, 40.5, 41.5,
        42.0, 42.5, 42.0, 41.0, 39.5, 37.5,
        35.5, 34.0, 32.5, 31.0, 30.0, 29.0,
    ]
    phoenix_carbon = [
        420.0, 410.0, 400.0, 390.0, 380.0, 360.0,
        280.0, 180.0, 90.0, 50.0, 40.0, 35.0,
        35.0, 40.0, 60.0, 110.0, 220.0, 340.0,
        430.0, 440.0, 435.0, 430.0, 425.0, 420.0,
    ]
    phoenix_prices = [
        0.08, 0.08, 0.07, 0.07, 0.07, 0.08,
        0.10, 0.09, 0.06, 0.05, 0.04, 0.04,
        0.04, 0.04, 0.05, 0.07, 0.12, 0.18,
        0.22, 0.24, 0.20, 0.15, 0.11, 0.09,
    ]
    phoenix_conditions = [
        HourlyEnvironmentalCondition(
            hour=h,
            temperature_c=phoenix_temps[h],
            carbon_intensity_g_per_kwh=phoenix_carbon[h],
            electricity_price_per_kwh=phoenix_prices[h],
            grid_water_intensity_l_per_kwh=0.5,  # Solar/gas mix has low grid water
        )
        for h in range(24)
    ]

    # 2. Quincy, WA: Cool climate, clean hydro carbon, high dam reservoir EWIF
    quincy_temps = [
        15.0, 14.5, 14.0, 14.0, 14.5, 15.5,
        17.0, 18.5, 20.0, 21.5, 22.5, 23.5,
        24.0, 24.5, 24.0, 23.0, 22.0, 20.5,
        19.0, 18.0, 17.0, 16.5, 16.0, 15.5,
    ]
    quincy_carbon = [
        65.0, 65.0, 60.0, 60.0, 65.0, 70.0,
        75.0, 75.0, 70.0, 65.0, 65.0, 60.0,
        60.0, 60.0, 65.0, 70.0, 75.0, 80.0,
        80.0, 75.0, 70.0, 70.0, 65.0, 65.0,
    ]
    quincy_prices = [
        0.05, 0.05, 0.05, 0.05, 0.05, 0.06,
        0.06, 0.07, 0.07, 0.06, 0.06, 0.06,
        0.06, 0.06, 0.06, 0.07, 0.07, 0.08,
        0.08, 0.07, 0.06, 0.06, 0.05, 0.05,
    ]
    quincy_conditions = [
        HourlyEnvironmentalCondition(
            hour=h,
            temperature_c=quincy_temps[h],
            carbon_intensity_g_per_kwh=quincy_carbon[h],
            electricity_price_per_kwh=quincy_prices[h],
            grid_water_intensity_l_per_kwh=4.2,  # Hydro dams have high surface evaporation
        )
        for h in range(24)
    ]

    # 3. Council Bluffs, IA: Moderate climate, nighttime wind peak (low night carbon)
    cb_temps = [
        19.0, 18.5, 18.0, 18.0, 18.5, 20.0,
        22.0, 24.5, 26.5, 28.0, 29.5, 30.5,
        31.0, 31.5, 31.0, 30.0, 28.5, 27.0,
        25.0, 23.5, 22.0, 21.0, 20.0, 19.5,
    ]
    cb_carbon = [
        90.0, 85.0, 80.0, 85.0, 95.0, 130.0,
        180.0, 240.0, 280.0, 310.0, 320.0, 330.0,
        335.0, 330.0, 320.0, 310.0, 290.0, 260.0,
        220.0, 170.0, 140.0, 120.0, 105.0, 95.0,
    ]
    cb_prices = [
        0.04, 0.04, 0.03, 0.03, 0.04, 0.06,
        0.08, 0.10, 0.12, 0.14, 0.15, 0.15,
        0.16, 0.16, 0.15, 0.14, 0.13, 0.12,
        0.11, 0.09, 0.07, 0.06, 0.05, 0.04,
    ]
    cb_conditions = [
        HourlyEnvironmentalCondition(
            hour=h,
            temperature_c=cb_temps[h],
            carbon_intensity_g_per_kwh=cb_carbon[h],
            electricity_price_per_kwh=cb_prices[h],
            grid_water_intensity_l_per_kwh=1.8,
        )
        for h in range(24)
    ]

    return {
        "phoenix-01": SiteEnvironmentalProfile(
            site_id="phoenix-01", hourly_conditions=phoenix_conditions
        ),
        "quincy-01": SiteEnvironmentalProfile(
            site_id="quincy-01", hourly_conditions=quincy_conditions
        ),
        "council-bluffs-01": SiteEnvironmentalProfile(
            site_id="council-bluffs-01", hourly_conditions=cb_conditions
        ),
    }


def get_default_workloads() -> list[Workload]:
    """Return a canonical batch of 5 heterogeneous AI workloads."""
    return [
        Workload(
            id="job-01",
            name="LLM Llama-3 70B Fine-Tuning",
            arrival_hour=1,
            duration_hours=6,
            gpus_required=32,
            deadline_hour=18,
            priority=4,
            is_preemptible=True,  # Checkpoint-resumable
        ),
        Workload(
            id="job-02",
            name="Autonomous Driving Vision Training",
            arrival_hour=8,
            duration_hours=3,
            gpus_required=16,
            deadline_hour=13,  # Urgent deadline
            priority=5,
            is_preemptible=False,  # Continuous execution required
        ),
        Workload(
            id="job-03",
            name="Recommendation Engine Daily Batch",
            arrival_hour=18,
            duration_hours=4,
            gpus_required=24,
            deadline_hour=24,  # Overnight window
            priority=3,
            is_preemptible=False,
        ),
        Workload(
            id="job-04",
            name="Speech Recognition Audio Evaluation",
            arrival_hour=11,
            duration_hours=2,
            gpus_required=8,
            deadline_hour=16,
            priority=2,
            is_preemptible=True,
        ),
        Workload(
            id="job-05",
            name="Reinforcement Learning Policy Search",
            arrival_hour=4,
            duration_hours=4,
            gpus_required=16,
            deadline_hour=20,
            priority=3,
            is_preemptible=True,
        ),
    ]
