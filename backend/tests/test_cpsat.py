"""Unit and integration tests for AquaGrid Google OR-Tools CP-SAT Optimizer."""

import pytest
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)
from src.scheduling.cpsat import CPSATScheduler
from src.models import Workload


@pytest.fixture
def benchmark_data():
    sites = get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = get_default_workloads()
    return sites, profiles, workloads


class TestCPSATSchedulerBasics:
    """Core functionality and contract validation for CPSATScheduler."""

    def test_scheduler_name(self):
        scheduler = CPSATScheduler()
        assert scheduler.name == "AquaGrid CP-SAT Optimizer"

    def test_weight_validation(self):
        # Must be non-negative
        with pytest.raises(AssertionError):
            CPSATScheduler(alpha=-0.1, beta=0.5, gamma=0.6)

        # Must sum to 1.0
        with pytest.raises(AssertionError):
            CPSATScheduler(alpha=0.5, beta=0.5, gamma=0.5)

    def test_solves_canonical_benchmark_to_optimal(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        scheduler = CPSATScheduler()
        result = scheduler.schedule(sites, profiles, workloads)

        assert result.status in ("OPTIMAL", "FEASIBLE")
        assert result.metrics.jobs_scheduled == len(workloads)
        assert result.metrics.jobs_unscheduled == 0
        assert result.metrics.deadline_violations == 0
        assert result.metrics.water_budget_violations_liters == 0.0
        assert result.solve_time_seconds > 0.0

    def test_gpu_capacity_never_exceeded_any_hour(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        scheduler = CPSATScheduler()
        result = scheduler.schedule(sites, profiles, workloads)

        site_caps = {s.id: s.gpu_capacity for s in sites}
        hourly_usage = {s.id: [0] * 24 for s in sites}

        for exc in result.executions:
            hourly_usage[exc.site_id][exc.hour] += exc.gpus_used

        for s_id, hours in hourly_usage.items():
            cap = site_caps[s_id]
            for h, used in enumerate(hours):
                assert used <= cap, f"Site {s_id} exceeded capacity at hour {h}: {used} > {cap}"


class TestCPSATHardConstraints:
    """Rigorous verification of hard physical and operational constraints."""

    def test_enforces_strict_water_budget(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        # Constrain Phoenix water budget to 400 L (tight limit)
        phoenix = next(s for s in sites if s.id == "phoenix-01")
        phoenix.daily_water_budget_liters = 400.0

        scheduler = CPSATScheduler(enforce_water_budget=True)
        result = scheduler.schedule(sites, profiles, workloads)

        assert result.status in ("OPTIMAL", "FEASIBLE")
        assert result.metrics.water_budget_violations_liters == 0.0
        phoenix_water = result.metrics.site_water_consumption.get("phoenix-01", 0.0)
        assert phoenix_water <= 400.0, f"Phoenix used {phoenix_water} L, exceeding 400 L limit"

    def test_non_preemptible_jobs_run_contiguously(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        scheduler = CPSATScheduler()
        result = scheduler.schedule(sites, profiles, workloads)

        workload_map = {w.id: w for w in workloads}
        for ws in result.workload_schedules:
            job = workload_map[ws.workload_id]
            if not job.is_preemptible:
                # Allocated hours must be strictly contiguous (e.g. [8, 9, 10])
                hours = sorted(ws.allocated_hours)
                expected_contiguous = list(range(min(hours), max(hours) + 1))
                assert hours == expected_contiguous, (
                    f"Non-preemptible job {job.id} had non-contiguous allocation: {hours}"
                )
                assert len(hours) == job.duration_hours

    def test_single_site_execution_rule(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        scheduler = CPSATScheduler()
        result = scheduler.schedule(sites, profiles, workloads)

        for job in workloads:
            job_executions = [e for e in result.executions if e.workload_id == job.id]
            sites_used = {e.site_id for e in job_executions}
            assert len(sites_used) == 1, (
                f"Job {job.id} executed across multiple sites: {sites_used}"
            )

    def test_impossible_budget_returns_infeasible_without_crash(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        # Set all budgets to 0.01 Liters (physically impossible)
        for s in sites:
            s.daily_water_budget_liters = 0.01

        scheduler = CPSATScheduler(enforce_water_budget=True)
        result = scheduler.schedule(sites, profiles, workloads)

        assert result.status == "INFEASIBLE"
        assert result.metrics.jobs_scheduled == 0
        assert result.metrics.jobs_unscheduled == len(workloads)
