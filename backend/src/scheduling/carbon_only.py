"""Baseline 2: Carbon-Only Minimizing Scheduler.

Algorithm:
1. Sort workloads by priority (descending) and arrival hour (ascending).
2. For each workload, evaluate every possible (site, start_hour) window
   within the workload's allowed [arrival_hour, deadline_hour] window.
3. For each candidate window where the site has enough free GPUs for all
   consecutive hours of duration:
   - Calculate the total carbon emissions (kg CO2) for running the job there.
4. Place the workload in the valid window that yields the MINIMUM total carbon.
5. Intentionally ignore water budgets and ambient temperature during decision-making.
   This demonstrates the real-world 'carbon-water tradeoff': minimizing carbon
   alone causes dangerous water consumption spikes in hot desert climates (e.g. Phoenix).
"""

from src.models import (
    DatacenterSite,
    SiteEnvironmentalProfile,
    Workload,
    HourlyExecution,
    WorkloadSchedule,
    ScheduleResult,
)
from src.simulation.calculator import calculate_hourly_execution
from src.scheduling.base import BaseScheduler


class CarbonOnlyScheduler(BaseScheduler):
    """Greedy Carbon-Only baseline scheduler.

    Selects the site and start time that minimizes total carbon emissions (kg CO2),
    while completely ignoring water consumption and water budgets.
    """

    @property
    def name(self) -> str:
        return "Baseline-2 Carbon-Only"

    def _run(
        self,
        sites: list[DatacenterSite],
        profiles: dict[str, SiteEnvironmentalProfile],
        workloads: list[Workload],
    ) -> ScheduleResult:
        # Sort workloads: high-priority jobs get first pick of the greenest slots
        sorted_jobs = sorted(workloads, key=lambda w: (-w.priority, w.arrival_hour))

        # GPU capacity tracker: gpu_used[site_id][hour]
        gpu_used: dict[str, list[int]] = {
            site.id: [0] * 24 for site in sites
        }

        all_executions: list[HourlyExecution] = []
        workload_schedules: list[WorkloadSchedule] = []

        for job in sorted_jobs:
            best_placement = self._find_lowest_carbon_slot(
                job=job,
                sites=sites,
                profiles=profiles,
                gpu_used=gpu_used,
            )

            if best_placement is None:
                # No site had enough GPU capacity before deadline
                workload_schedules.append(
                    WorkloadSchedule(
                        workload_id=job.id,
                        scheduled=False,
                        site_id=None,
                        start_hour=None,
                        finish_hour=None,
                        allocated_hours=[],
                        deadline_met=False,
                        rejection_reason="No site had sufficient GPU capacity within the deadline window.",
                    )
                )
                continue

            site_id, start_hour, candidate_slices = best_placement
            finish_hour = start_hour + job.duration_hours
            allocated_hours = list(range(start_hour, finish_hour))
            deadline_met = finish_hour <= job.deadline_hour

            # Deduct GPUs
            for h in allocated_hours:
                gpu_used[site_id][h] += job.gpus_required

            # Add execution slices
            all_executions.extend(candidate_slices)

            # Record schedule
            workload_schedules.append(
                WorkloadSchedule(
                    workload_id=job.id,
                    scheduled=True,
                    site_id=site_id,
                    start_hour=start_hour,
                    finish_hour=finish_hour,
                    allocated_hours=allocated_hours,
                    deadline_met=deadline_met,
                    rejection_reason=None if deadline_met
                    else f"Finished at hour {finish_hour}, deadline was {job.deadline_hour}",
                )
            )

        metrics = self._aggregate_metrics(all_executions, workload_schedules, sites)

        return ScheduleResult(
            scheduler_name=self.name,
            status="FEASIBLE",
            executions=all_executions,
            workload_schedules=workload_schedules,
            metrics=metrics,
            solve_time_seconds=0.0,
        )

    def _find_lowest_carbon_slot(
        self,
        job: Workload,
        sites: list[DatacenterSite],
        profiles: dict[str, SiteEnvironmentalProfile],
        gpu_used: dict[str, list[int]],
    ) -> tuple[str, int, list[HourlyExecution]] | None:
        """Evaluate all feasible (site, start_hour) slots and return the one with minimal carbon."""
        best_slot = None
        min_carbon = float("inf")

        latest_start = job.deadline_hour - job.duration_hours

        for site in sites:
            profile = profiles.get(site.id)
            if profile is None:
                continue

            for start in range(job.arrival_hour, latest_start + 1):
                if start + job.duration_hours > 24:
                    break

                block_hours = range(start, start + job.duration_hours)

                # Check GPU availability for all hours of the duration
                if not all(
                    gpu_used[site.id][h] + job.gpus_required <= site.gpu_capacity
                    for h in block_hours
                ):
                    continue

                # Feasible slot! Calculate carbon for this candidate window
                candidate_slices: list[HourlyExecution] = []
                candidate_carbon = 0.0

                for h in block_hours:
                    condition = profile.get_hour(h)
                    exec_slice = calculate_hourly_execution(
                        site=site,
                        workload_id=job.id,
                        gpus_used=job.gpus_required,
                        hour=h,
                        condition=condition,
                    )
                    candidate_slices.append(exec_slice)
                    candidate_carbon += exec_slice.carbon_kg

                # Minimize carbon (tie-break on earlier start, then site.id)
                if candidate_carbon < min_carbon:
                    min_carbon = candidate_carbon
                    best_slot = (site.id, start, candidate_slices)

        return best_slot
