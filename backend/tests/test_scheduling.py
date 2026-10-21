"""Unit tests for scheduling algorithms."""

import pytest

from src.scheduling.fifo import FIFOScheduler
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)
from src.models import Workload, DatacenterSite, CoolingTechnology


@pytest.fixture
def sites():
    return get_default_sites()


@pytest.fixture
def profiles():
    return get_default_environmental_profiles()


@pytest.fixture
def workloads():
    return get_default_workloads()


@pytest.fixture
def scheduler():
    return FIFOScheduler()


class TestFIFOSchedulerBasics:
    """Tests for basic FIFO scheduling behaviour."""

    def test_scheduler_has_correct_name(self, scheduler):
        assert scheduler.name == "Baseline-1 FIFO"

    def test_all_jobs_scheduled_on_sufficient_capacity(
        self, scheduler, sites, profiles, workloads
    ):
        """With 128 GPUs available and only 5 jobs, all should be scheduled."""
        result = scheduler.schedule(sites, profiles, workloads)

        assert result.status == "FEASIBLE"
        assert result.metrics.jobs_scheduled == 5
        assert result.metrics.jobs_unscheduled == 0

    def test_result_contains_executions(
        self, scheduler, sites, profiles, workloads
    ):
        """Every scheduled job must produce at least one hourly execution record."""
        result = scheduler.schedule(sites, profiles, workloads)

        scheduled_ids = {
            s.workload_id for s in result.workload_schedules if s.scheduled
        }
        execution_ids = {e.workload_id for e in result.executions}

        assert scheduled_ids == execution_ids

    def test_solve_time_is_recorded(
        self, scheduler, sites, profiles, workloads
    ):
        """Solve time must be a positive float."""
        result = scheduler.schedule(sites, profiles, workloads)
        assert result.solve_time_seconds > 0.0

    def test_metrics_are_positive(
        self, scheduler, sites, profiles, workloads
    ):
        """All energy, water, carbon, and cost metrics must be positive."""
        m = scheduler.schedule(sites, profiles, workloads).metrics
        assert m.total_it_energy_kwh > 0
        assert m.total_facility_energy_kwh > 0
        assert m.total_direct_water_liters > 0
        assert m.total_carbon_kg > 0
        assert m.total_cost_usd > 0

    def test_facility_energy_exceeds_it_energy(
        self, scheduler, sites, profiles, workloads
    ):
        """Total facility energy must always be >= IT energy (PUE >= 1.0)."""
        m = scheduler.schedule(sites, profiles, workloads).metrics
        assert m.total_facility_energy_kwh >= m.total_it_energy_kwh


class TestFIFOOrderAndCapacity:
    """Tests verifying FIFO ordering and GPU capacity enforcement."""

    def test_jobs_respect_gpu_capacity(
        self, scheduler, sites, profiles, workloads
    ):
        """At no hour should GPU usage exceed the site's capacity."""
        result = scheduler.schedule(sites, profiles, workloads)

        site_map = {s.id: s for s in sites}
        # Build per-site, per-hour GPU usage from executions
        hourly_gpu: dict[str, list[int]] = {s.id: [0] * 24 for s in sites}
        for sched in result.workload_schedules:
            if sched.scheduled:
                for h in sched.allocated_hours:
                    hourly_gpu[sched.site_id][h] += next(
                        w.gpus_required
                        for w in workloads
                        if w.id == sched.workload_id
                    )

        for site_id, usage in hourly_gpu.items():
            capacity = site_map[site_id].gpu_capacity
            for h, used in enumerate(usage):
                assert used <= capacity, (
                    f"Site {site_id} exceeded GPU capacity at hour {h}: "
                    f"{used} > {capacity}"
                )

    def test_jobs_start_after_arrival(
        self, scheduler, sites, profiles, workloads
    ):
        """No job should start before its arrival hour."""
        result = scheduler.schedule(sites, profiles, workloads)
        workload_map = {w.id: w for w in workloads}

        for sched in result.workload_schedules:
            if sched.scheduled:
                job = workload_map[sched.workload_id]
                assert sched.start_hour >= job.arrival_hour, (
                    f"Job {job.id} started at hour {sched.start_hour} "
                    f"but arrived at hour {job.arrival_hour}"
                )

    def test_unschedulable_job_is_reported_not_dropped(self):
        """A job that cannot fit must be recorded as unscheduled, never silently dropped."""
        # Create a tiny site with only 4 GPUs
        tiny_site = DatacenterSite(
            id="tiny-site",
            name="Tiny Test Site",
            location="Nowhere",
            gpu_capacity=4,
            daily_water_budget_liters=99999.0,
        )
        # Create a job that needs 32 GPUs (impossible on tiny-site)
        impossible_job = Workload(
            id="impossible",
            name="Impossible Job",
            arrival_hour=0,
            duration_hours=2,
            gpus_required=32,  # Way more than 4 GPU capacity!
            deadline_hour=5,
        )
        profiles = get_default_environmental_profiles()
        tiny_profile = {
            "tiny-site": profiles["phoenix-01"].model_copy(
                update={"site_id": "tiny-site"}
            )
        }

        result = FIFOScheduler().schedule([tiny_site], tiny_profile, [impossible_job])

        assert result.metrics.jobs_unscheduled == 1
        assert result.metrics.jobs_scheduled == 0

        unscheduled = result.workload_schedules[0]
        assert unscheduled.scheduled is False
        assert unscheduled.rejection_reason is not None
