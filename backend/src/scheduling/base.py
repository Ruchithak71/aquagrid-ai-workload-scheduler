"""Abstract base class that every AquaGrid scheduler must implement."""

import time
from abc import ABC, abstractmethod

from src.models import (
    DatacenterSite,
    SiteEnvironmentalProfile,
    Workload,
    ScheduleResult,
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
