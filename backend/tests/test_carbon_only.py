"""Tests for Baseline 2: Carbon-Only Minimizing Scheduler."""

import pytest
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)
from src.scheduling.fifo import FIFOScheduler
from src.scheduling.carbon_only import CarbonOnlyScheduler
from src.models import Workload


@pytest.fixture
def benchmark_data():
    sites = get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = get_default_workloads()
    return sites, profiles, workloads


class TestCarbonOnlySchedulerBasics:
    """Basic functional tests for CarbonOnlyScheduler."""

    def test_scheduler_name(self):
        scheduler = CarbonOnlyScheduler()
        assert scheduler.name == "Baseline-2 Carbon-Only"

    def test_all_canonical_jobs_scheduled(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        scheduler = CarbonOnlyScheduler()
        result = scheduler.schedule(sites, profiles, workloads)

        assert result.status == "FEASIBLE"
        assert result.metrics.jobs_scheduled == len(workloads)
        assert result.metrics.jobs_unscheduled == 0
        assert result.metrics.deadline_violations == 0
        assert result.solve_time_seconds >= 0.0

    def test_gpu_capacity_never_exceeded(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        scheduler = CarbonOnlyScheduler()
        result = scheduler.schedule(sites, profiles, workloads)

        # Track hourly GPU usage per site from executions
        site_caps = {s.id: s.gpu_capacity for s in sites}
        hourly_usage = {s.id: [0] * 24 for s in sites}

        for exc in result.executions:
            hourly_usage[exc.site_id][exc.hour] += exc.gpus_used

        for site_id, hours in hourly_usage.items():
            cap = site_caps[site_id]
            for h, used in enumerate(hours):
                assert used <= cap, f"Site {site_id} exceeded capacity at hour {h}: {used} > {cap}"

    def test_job_deadlines_respected(self, benchmark_data):
        sites, profiles, workloads = benchmark_data
        scheduler = CarbonOnlyScheduler()
        result = scheduler.schedule(sites, profiles, workloads)

        workload_map = {w.id: w for w in workloads}
        for ws in result.workload_schedules:
            job = workload_map[ws.workload_id]
            assert ws.start_hour >= job.arrival_hour
            assert ws.finish_hour <= job.deadline_hour
            assert ws.deadline_met is True


class TestCarbonWaterTradeoffComparison:
    """Verifies that Carbon-Only minimizes carbon relative to FIFO,
    while highlighting the trade-off with water consumption."""

    def test_carbon_only_beats_or_matches_fifo_emissions(self, benchmark_data):
        sites, profiles, workloads = benchmark_data

        fifo_result = FIFOScheduler().schedule(sites, profiles, workloads)
        carbon_result = CarbonOnlyScheduler().schedule(sites, profiles, workloads)

        # Carbon-Only must achieve lower (or equal) carbon emissions than naive FIFO
        assert carbon_result.metrics.total_carbon_kg <= fifo_result.metrics.total_carbon_kg

    def test_unschedulable_job_reported_honestly(self, benchmark_data):
        sites, profiles, _ = benchmark_data

        impossible_job = Workload(
            id="job-giant",
            name="Impossible Cluster",
            gpus_required=500,  # Phoenix has 128, Quincy 96, Council Bluffs 128
            duration_hours=2,
            arrival_hour=0,
            deadline_hour=24,
            priority=5,
            is_preemptible=False,
        )

        scheduler = CarbonOnlyScheduler()
        result = scheduler.schedule(sites, profiles, [impossible_job])

        assert result.metrics.jobs_scheduled == 0
        assert result.metrics.jobs_unscheduled == 1
        assert result.workload_schedules[0].scheduled is False
        assert "capacity" in result.workload_schedules[0].rejection_reason.lower()
