"""Pareto Frontier exploration and Optimization Presets for AquaGrid.

Provides pre-configured multi-objective weighting profiles and tools to sweep
the trade-off curve between electricity cost, carbon emissions, and water consumption.
"""

from enum import Enum
from typing import NamedTuple

from src.models import DatacenterSite, SiteEnvironmentalProfile, Workload, ScheduleResult
from src.scheduling.cpsat import CPSATScheduler


class OptimizationPreset(str, Enum):
    """Standard operational profiles for datacenter workload management."""

    BALANCED = "balanced"
    COST_FIRST = "cost_first"
    CARBON_FIRST = "carbon_first"
    WATER_FIRST = "water_first"


class PresetWeights(NamedTuple):
    alpha: float  # Cost weight
    beta: float   # Carbon weight
    gamma: float  # Water weight
    description: str


PRESET_CONFIGS: dict[OptimizationPreset, PresetWeights] = {
    OptimizationPreset.BALANCED: PresetWeights(
        alpha=0.33,
        beta=0.33,
        gamma=0.34,
        description="Balanced trade-off between operational cost, carbon emissions, and water usage.",
    ),
    OptimizationPreset.COST_FIRST: PresetWeights(
        alpha=0.80,
        beta=0.10,
        gamma=0.10,
        description="Prioritizes minimizing financial electricity costs, placing jobs in cheapest tariff hours.",
    ),
    OptimizationPreset.CARBON_FIRST: PresetWeights(
        alpha=0.10,
        beta=0.80,
        gamma=0.10,
        description="Aggressively targets near-zero grid carbon intensity (e.g. peak solar and wind).",
    ),
    OptimizationPreset.WATER_FIRST: PresetWeights(
        alpha=0.10,
        beta=0.10,
        gamma=0.80,
        description="Maximizes water conservation, shifting jobs away from hot evaporative cooling towers.",
    ),
}


def get_preset_scheduler(
    preset: OptimizationPreset,
    enforce_water_budget: bool = True,
    time_limit_seconds: float = 10.0,
) -> CPSATScheduler:
    """Instantiate a CPSATScheduler configured with a standard operational preset."""
    weights = PRESET_CONFIGS[preset]
    return CPSATScheduler(
        alpha=weights.alpha,
        beta=weights.beta,
        gamma=weights.gamma,
        enforce_water_budget=enforce_water_budget,
        time_limit_seconds=time_limit_seconds,
    )


def run_preset(
    preset: OptimizationPreset,
    sites: list[DatacenterSite],
    profiles: dict[str, SiteEnvironmentalProfile],
    workloads: list[Workload],
    enforce_water_budget: bool = True,
    time_limit_seconds: float = 10.0,
) -> ScheduleResult:
    """Execute CP-SAT optimization under a specific named preset."""
    scheduler = get_preset_scheduler(
        preset=preset,
        enforce_water_budget=enforce_water_budget,
        time_limit_seconds=time_limit_seconds,
    )
    result = scheduler.schedule(sites, profiles, workloads)
    # Add human-readable preset notes
    return result.model_copy(
        update={
            "notes": f"Optimization Preset: {preset.value.upper()} ({PRESET_CONFIGS[preset].description})"
        }
    )


def sweep_pareto_frontier(
    sites: list[DatacenterSite],
    profiles: dict[str, SiteEnvironmentalProfile],
    workloads: list[Workload],
    presets: list[OptimizationPreset] | None = None,
    enforce_water_budget: bool = True,
) -> dict[str, ScheduleResult]:
    """Execute optimization across all presets to compare trade-off outcomes."""
    selected_presets = presets or list(OptimizationPreset)
    results: dict[str, ScheduleResult] = {}

    for preset in selected_presets:
        results[preset.value] = run_preset(
            preset=preset,
            sites=sites,
            profiles=profiles,
            workloads=workloads,
            enforce_water_budget=enforce_water_budget,
        )

    return results
