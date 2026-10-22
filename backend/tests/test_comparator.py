"""Unit tests for the Comparative Benchmark Engine."""

import pytest
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)
from src.simulation.comparator import compare_schedulers


@pytest.fixture
def benchmark_data():
    sites = get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = get_default_workloads()
    return sites, profiles, workloads


class TestComparativeBenchmarkEngine:
    """Verifies that compare_schedulers generates accurate benchmark reports."""

    def test_compare_schedulers_executes_all_models(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        report = compare_schedulers(sites, profiles, workloads)

        expected_names = {
            "FIFO",
            "Carbon-Only",
            "CP-SAT (Balanced)",
            "CP-SAT (Water-First)",
            "CP-SAT (Carbon-First)",
            "CP-SAT (Cost-First)",
        }
        actual_names = {r.scheduler_name for r in report.comparison_table}
        assert expected_names.issubset(actual_names)
        assert report.feasibility.is_feasible is True

    def test_identifies_category_winners(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        report = compare_schedulers(sites, profiles, workloads)

        assert report.winner_for_carbon in [r.scheduler_name for r in report.comparison_table]
        assert report.winner_for_water in [r.scheduler_name for r in report.comparison_table]
        assert report.winner_for_cost in [r.scheduler_name for r in report.comparison_table]

    def test_carbon_savings_percentage_calculated(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        report = compare_schedulers(sites, profiles, workloads)

        bal_row = next(r for r in report.comparison_table if r.scheduler_name == "CP-SAT (Balanced)")
        # AquaGrid Balanced achieves > 50% carbon reduction vs FIFO on this dataset
        assert bal_row.carbon_savings_pct_vs_fifo > 50.0

    def test_flags_water_budget_violations_honestly(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        # Set Phoenix water budget to 400 L
        sites[0].daily_water_budget_liters = 400.0

        report = compare_schedulers(sites, profiles, workloads, enforce_water_budget=True)

        co_row = next(r for r in report.comparison_table if r.scheduler_name == "Carbon-Only")
        bal_row = next(r for r in report.comparison_table if r.scheduler_name == "CP-SAT (Balanced)")

        # Carbon-Only exceeds 400 L, so it must not be compliant
        assert co_row.is_budget_compliant is False
        assert co_row.water_budget_violations_liters > 0.0

        # AquaGrid CP-SAT must be compliant
        assert bal_row.is_budget_compliant is True
        assert bal_row.water_budget_violations_liters == 0.0

    def test_key_findings_generated(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        report = compare_schedulers(sites, profiles, workloads)

        assert len(report.key_findings) >= 2
        for finding in report.key_findings:
            assert len(finding) > 10
