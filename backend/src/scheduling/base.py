"""Abstract base class that every AquaGrid scheduler must implement."""

import time
from abc import ABC, abstractmethod

from src.models import (
    DatacenterSite,
    SiteEnvironmentalProfile,
    Workload,
    ScheduleResult,
    HourlyExecution,
    WorkloadSchedule,
    ScheduleMetrics,
)


class BaseScheduler(ABC):
    """Blueprint that all AquaGrid schedulers must follow.

    Every concrete scheduler (FIFO, Carbon-Only, CP-SAT Optimizer) must
    implement the `schedule()` method and may optionally override `name`.

    Think of this like a contract: if you claim to be an AquaGrid scheduler,
    you MUST be able to accept sites + profiles + workloads and return a
    ScheduleResult. Python enforces this at class-creation time.
    """

    @property
    def name(self) -> str:
        """Human-readable scheduler name used in ScheduleResult output."""
        return self.__class__.__name__

    @abstractmethod
    def _run(
        self,
        sites: list[DatacenterSite],
        profiles: dict[str, SiteEnvironmentalProfile],
        workloads: list[Workload],
    ) -> ScheduleResult:
        """Core scheduling logic. Subclasses must implement this."""
        ...

    def schedule(
        self,
        sites: list[DatacenterSite],
        profiles: dict[str, SiteEnvironmentalProfile],
        workloads: list[Workload],
    ) -> ScheduleResult:
        """Public entry point. Runs _run() and injects wall-clock solve time."""
        start = time.perf_counter()
        result = self._run(sites, profiles, workloads)
        elapsed = round(time.perf_counter() - start, 4)
        # Inject actual solve time without mutating user's result object
        return result.model_copy(update={"solve_time_seconds": elapsed})

    @staticmethod
    def _aggregate_metrics(
        executions: list[HourlyExecution],
        schedules: list[WorkloadSchedule],
        sites: list[DatacenterSite],
    ) -> ScheduleMetrics:
        """Sum up all hourly execution slices into aggregate metrics."""
        total_it_energy = sum(e.it_energy_kwh for e in executions)
        total_facility_energy = sum(e.total_energy_kwh for e in executions)
        total_direct_water = sum(e.direct_water_liters for e in executions)
        total_indirect_water = sum(e.indirect_water_liters for e in executions)
        total_carbon = sum(e.carbon_kg for e in executions)
        total_cost = sum(e.cost_usd for e in executions)

        jobs_scheduled = sum(1 for s in schedules if s.scheduled)
        jobs_unscheduled = sum(1 for s in schedules if not s.scheduled)
        deadline_violations = sum(
            1 for s in schedules if s.scheduled and not s.deadline_met
        )

        site_water: dict[str, float] = {site.id: 0.0 for site in sites}
        for e in executions:
            site_water[e.site_id] = site_water.get(e.site_id, 0.0) + e.direct_water_liters

        site_budgets = {site.id: site.daily_water_budget_liters for site in sites}
        water_violations = sum(
            max(0.0, used - site_budgets.get(sid, float("inf")))
            for sid, used in site_water.items()
        )

        return ScheduleMetrics(
            total_it_energy_kwh=round(total_it_energy, 4),
            total_facility_energy_kwh=round(total_facility_energy, 4),
            total_direct_water_liters=round(total_direct_water, 4),
            total_indirect_water_liters=round(total_indirect_water, 4),
            total_water_liters=round(total_direct_water + total_indirect_water, 4),
            total_carbon_kg=round(total_carbon, 4),
            total_cost_usd=round(total_cost, 4),
            jobs_scheduled=jobs_scheduled,
            jobs_unscheduled=jobs_unscheduled,
            deadline_violations=deadline_violations,
            water_budget_violations_liters=round(water_violations, 4),
            site_water_consumption={sid: round(v, 4) for sid, v in site_water.items()},
        )
