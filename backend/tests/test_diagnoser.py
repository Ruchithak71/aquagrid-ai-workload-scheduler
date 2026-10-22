"""Unit tests for the Infeasibility Diagnoser."""

import pytest
from src.models import Workload
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)
from src.simulation.diagnoser import diagnose_scenario


@pytest.fixture
def benchmark_data():
    sites = get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = get_default_workloads()
    return sites, profiles, workloads


class TestInfeasibilityDiagnoser:
    """Verifies pre-flight feasibility detection and diagnostics."""

    def test_default_scenario_is_feasible(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        report = diagnose_scenario(sites, profiles, workloads)

        assert report.is_feasible is True
        assert len(report.critical_issues) == 0
        assert report.network_utilization_pct > 0.0
        assert report.network_utilization_pct < 50.0

    def test_detects_impossible_deadline_window(self, benchmark_data):
        sites, profiles, _ = benchmark_data
        # Use model_construct to simulate bypassed validation from external/legacy data
        impossible_job = Workload.model_construct(
            id="job-tight",
            name="Impossible Window",
            gpus_required=8,
            duration_hours=5,
            arrival_hour=10,
            deadline_hour=12,  # Window is only 2h, but duration is 5h!
            priority=3,
        )

        report = diagnose_scenario(sites, profiles, [impossible_job])
        assert report.is_feasible is False
        assert any(i.category == "TIME_WINDOW" for i in report.critical_issues)

    def test_detects_excessive_gpu_demand(self, benchmark_data):
        sites, profiles, _ = benchmark_data
        huge_job = Workload(
            id="job-huge",
            name="Massive Cluster",
            gpus_required=500,  # Largest site has 128
            duration_hours=2,
            arrival_hour=0,
            deadline_hour=24,
            priority=5,
        )

        report = diagnose_scenario(sites, profiles, [huge_job])
        assert report.is_feasible is False
        assert any(i.category == "GPU_CAPACITY" for i in report.critical_issues)

    def test_detects_network_overload(self, benchmark_data):
        sites, profiles, _ = benchmark_data
        # Network total capacity: (128 + 96 + 128) * 24 = 8448 GPU-hours
        # Create an army of massive workloads exceeding 8448 GPU-hours
        overload_jobs = [
            Workload(
                id=f"job-overload-{i}",
                name=f"Overload Batch {i}",
                gpus_required=100,
                duration_hours=20,  # 2000 GPU-hours each
                arrival_hour=0,
                deadline_hour=24,
                priority=1,
            )
            for i in range(6)  # 6 * 2000 = 12000 GPU-hours > 8448
        ]

        report = diagnose_scenario(sites, profiles, overload_jobs)
        assert report.is_feasible is False
        assert any(i.category == "NETWORK_OVERLOAD" for i in report.critical_issues)

    def test_flags_zero_scheduling_slack_warning(self, benchmark_data):
        sites, profiles, _ = benchmark_data
        tight_job = Workload(
            id="job-zero-slack",
            name="Zero Slack Job",
            gpus_required=16,
            duration_hours=4,
            arrival_hour=8,
            deadline_hour=12,  # Exactly 4 hours!
            priority=4,
        )

        report = diagnose_scenario(sites, profiles, [tight_job])
        assert report.is_feasible is True  # Feasible, but has a warning
        assert any(w.category == "TIME_WINDOW" and "zero scheduling slack" in w.message.lower() for w in report.warnings)
