"""Baseline 1: Greedy Earliest-Deadline-First / FIFO Scheduler.

Algorithm:
1. Sort workloads by arrival hour (first come, first served).
2. For each workload, find the earliest contiguous block of hours
   where a site has enough free GPUs.
3. Place the workload there immediately — no carbon, water, or cost awareness.
4. Track and report all resource metrics honestly, including any jobs
   that could not be scheduled (capacity violations) and any deadline misses.

This intentionally naive baseline reveals the environmental cost of
scheduling without water or carbon awareness.
"""

import time

from src.models import (
    DatacenterSite,
    SiteEnvironmentalProfile,
    Workload,
    HourlyExecution,
    WorkloadSchedule,
    ScheduleMetrics,
    ScheduleResult,
)
from src.simulation.calculator import calculate_hourly_execution
from src.scheduling.base import BaseScheduler


class FIFOScheduler(BaseScheduler):
    """Greedy FIFO (First-In, First-Out) baseline scheduler.

    Schedules jobs in arrival-time order on the first available site,
    ignoring carbon intensity, water budgets, and electricity prices.
    """

    @property
    def name(self) -> str:
        return "Baseline-1 FIFO"

    def _run(
        self,
        sites: list[DatacenterSite],
        profiles: dict[str, SiteEnvironmentalProfile],
        workloads: list[Workload],
    ) -> ScheduleResult:
        # -----------------------------------------------------------------
        # STEP 1: Sort jobs by arrival hour (FIFO = earliest arriving first)
        # -----------------------------------------------------------------
        sorted_jobs = sorted(workloads, key=lambda w: w.arrival_hour)

        # -----------------------------------------------------------------
        # STEP 2: Build a GPU availability table.
        #
        # `gpu_used[site_id][hour]` tells us how many GPUs are already
        # allocated at that site during that hour.
        # At the start, every site has 0 GPUs allocated at every hour.
        # -----------------------------------------------------------------
        gpu_used: dict[str, list[int]] = {
            site.id: [0] * 24 for site in sites
        }

        # Collect results
        all_executions: list[HourlyExecution] = []
        workload_schedules: list[WorkloadSchedule] = []

        # -----------------------------------------------------------------
        # STEP 3: Try to schedule each job
        # -----------------------------------------------------------------
        for job in sorted_jobs:
            placed = False  # Will become True once we find a valid slot

            # Try each site in the order they appear in the list
            for site in sites:
                profile = profiles.get(site.id)
                if profile is None:
                    continue  # Skip sites with no environmental data

                # Find the earliest valid start hour for this job on this site
                # A valid start hour means:
                #   - At or after the job's arrival
                #   - Enough consecutive hours before the deadline
                #   - Enough free GPUs at every hour in that block
                start_hour = self._find_earliest_start(
                    job, site, gpu_used[site.id]
                )

                if start_hour is None:
                    continue  # This site cannot fit the job — try the next one

                # -------------------------------------------------------
                # FOUND A SLOT — allocate the job here
                # -------------------------------------------------------
                allocated_hours = list(
                    range(start_hour, start_hour + job.duration_hours)
                )
                finish_hour = start_hour + job.duration_hours
                deadline_met = finish_hour <= job.deadline_hour

                # Mark GPUs as used during each allocated hour
                for h in allocated_hours:
                    gpu_used[site.id][h] += job.gpus_required

                # Compute hourly resource metrics for each execution slice
                for h in allocated_hours:
                    condition = profile.get_hour(h)
                    exec_slice = calculate_hourly_execution(
                        site=site,
                        workload_id=job.id,
                        gpus_used=job.gpus_required,
                        hour=h,
                        condition=condition,
                    )
                    all_executions.append(exec_slice)

                # Record the scheduling outcome for this job
                workload_schedules.append(
                    WorkloadSchedule(
                        workload_id=job.id,
                        scheduled=True,
                        site_id=site.id,
                        start_hour=start_hour,
                        finish_hour=finish_hour,
                        allocated_hours=allocated_hours,
                        deadline_met=deadline_met,
                        rejection_reason=None if deadline_met
                        else f"Finished at hour {finish_hour}, deadline was {job.deadline_hour}",
                    )
                )

                placed = True
                break  # Stop looking at other sites — job is placed!

            if not placed:
                # No site could fit this job — report it honestly
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

        # -----------------------------------------------------------------
        # STEP 4: Aggregate all metrics from the execution slices
        # -----------------------------------------------------------------
        metrics = self._aggregate_metrics(all_executions, workload_schedules, sites)

        return ScheduleResult(
            scheduler_name=self.name,
            status="FEASIBLE",
            executions=all_executions,
            workload_schedules=workload_schedules,
            metrics=metrics,
            solve_time_seconds=0.0,  # Will be overwritten by BaseScheduler.schedule()
        )

    def _find_earliest_start(
        self,
        job: Workload,
        site: DatacenterSite,
        gpu_used_at_site: list[int],
    ) -> int | None:
        """Find the earliest valid start hour for a non-preemptible job block.

        Scans from the job's arrival hour forward, looking for `duration_hours`
        consecutive hours where:
        - The hour is within the job's time window (arrival to deadline).
        - The site has enough free GPUs (capacity - currently used).

        Returns the start hour if found, or None if no slot exists.
        """
        # The latest possible start that still allows finishing before deadline
        latest_start = job.deadline_hour - job.duration_hours

        for start in range(job.arrival_hour, latest_start + 1):
            # Check every hour in the potential block
            block_hours = range(start, start + job.duration_hours)

            # All hours in the block must fit within the 24h horizon
            if start + job.duration_hours > 24:
                break

            # All hours must have enough free GPUs
            fits = all(
                gpu_used_at_site[h] + job.gpus_required <= site.gpu_capacity
                for h in block_hours
            )

            if fits:
                return start  # Found the earliest valid slot!

        return None  # No valid slot found on this site

    def _aggregate_metrics(
        self,
        executions: list[HourlyExecution],
        schedules: list[WorkloadSchedule],
        sites: list[DatacenterSite],
    ) -> ScheduleMetrics:
        """Sum up all hourly execution slices into aggregate metrics."""

        # Sum all per-hour resource fields across all executions
        total_it_energy = sum(e.it_energy_kwh for e in executions)
        total_facility_energy = sum(e.total_energy_kwh for e in executions)
        total_direct_water = sum(e.direct_water_liters for e in executions)
        total_indirect_water = sum(e.indirect_water_liters for e in executions)
        total_carbon = sum(e.carbon_kg for e in executions)
        total_cost = sum(e.cost_usd for e in executions)

        # Count scheduling outcomes
        jobs_scheduled = sum(1 for s in schedules if s.scheduled)
        jobs_unscheduled = sum(1 for s in schedules if not s.scheduled)
        deadline_violations = sum(
            1 for s in schedules if s.scheduled and not s.deadline_met
        )

        # Calculate per-site direct water totals and budget violations
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
