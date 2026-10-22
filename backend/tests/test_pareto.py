"""Tests for AquaGrid Optimization Presets and Pareto Frontier Sweeping."""

import pytest
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)
from src.scheduling.pareto import (
    OptimizationPreset,
    PRESET_CONFIGS,
    get_preset_scheduler,
    run_preset,
    sweep_pareto_frontier,
)


@pytest.fixture
def benchmark_data():
    sites = get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = get_default_workloads()
    return sites, profiles, workloads


class TestOptimizationPresets:
    """Validates preset definitions and weights."""

    def test_presets_exist_and_sum_to_one(self):
        for preset, weights in PRESET_CONFIGS.items():
            assert weights.alpha >= 0.0
            assert weights.beta >= 0.0
            assert weights.gamma >= 0.0
            total = weights.alpha + weights.beta + weights.gamma
            assert abs(total - 1.0) < 1e-3, f"Preset {preset} weights sum to {total}, expected 1.0"
            assert len(weights.description) > 0

    def test_get_preset_scheduler_instantiation(self):
        scheduler = get_preset_scheduler(OptimizationPreset.WATER_FIRST)
        assert scheduler.gamma == 0.80
        assert scheduler.alpha == 0.10
        assert scheduler.beta == 0.10

    def test_run_individual_preset(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        result = run_preset(
            preset=OptimizationPreset.BALANCED,
            sites=sites,
            profiles=profiles,
            workloads=workloads,
        )
        assert result.status in ("OPTIMAL", "FEASIBLE")
        assert result.metrics.jobs_scheduled == len(workloads)
        assert "BALANCED" in result.notes


class TestParetoFrontierSweeper:
    """Validates sweeping across multiple presets and trade-off dynamics."""

    def test_sweep_all_presets(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        frontier = sweep_pareto_frontier(
            sites=sites,
            profiles=profiles,
            workloads=workloads,
        )

        assert len(frontier) == len(OptimizationPreset)
        for preset_name, res in frontier.items():
            assert res.status in ("OPTIMAL", "FEASIBLE")
            assert res.metrics.jobs_scheduled == len(workloads)
            assert res.metrics.water_budget_violations_liters == 0.0

    def test_water_first_minimizes_water_relative_to_carbon_first(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        # Impose a 400 L water budget on Phoenix
        sites[0].daily_water_budget_liters = 400.0

        water_res = run_preset(OptimizationPreset.WATER_FIRST, sites, profiles, workloads)
        carbon_res = run_preset(OptimizationPreset.CARBON_FIRST, sites, profiles, workloads)

        # Water-First should consume less or equal water compared to Carbon-First
        assert water_res.metrics.total_water_liters <= carbon_res.metrics.total_water_liters
        assert water_res.metrics.water_budget_violations_liters == 0.0
        assert carbon_res.metrics.water_budget_violations_liters == 0.0

    def test_sweep_custom_subset(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        custom_presets = [OptimizationPreset.COST_FIRST, OptimizationPreset.WATER_FIRST]
        frontier = sweep_pareto_frontier(
            sites=sites,
            profiles=profiles,
            workloads=workloads,
            presets=custom_presets,
        )

        assert set(frontier.keys()) == {"cost_first", "water_first"}
