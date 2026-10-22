"""Google OR-Tools CP-SAT Constrained Multi-Objective Optimizer.

This is the core scientific optimization engine of AquaGrid.
Unlike greedy baselines (FIFO and Carbon-Only), this optimizer:
1. Evaluates all 24 hours, all sites, and all workloads SIMULTANEOUSLY.
2. Enforces hard mathematical constraints:
   - GPU capacity limits at every hour.
   - Workload arrival and deadline windows.
   - Single-site execution (no spatial fragmentation).
   - Contiguous execution blocks for non-preemptible jobs.
   - Local daily water budgets (guaranteed never violated!).
3. Minimizes a multi-objective trade-off function:
   min (alpha * Cost + beta * Carbon + gamma * Water)
"""

from ortools.sat.python import cp_model

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


class CPSATScheduler(BaseScheduler):
    """Water, Energy, and Carbon-Aware CP-SAT Optimizer."""

    def __init__(
        self,
        alpha: float = 0.33,  # Electricity cost weight
        beta: float = 0.33,   # Carbon emission weight
        gamma: float = 0.34,  # Water consumption weight
        enforce_water_budget: bool = True,
        time_limit_seconds: float = 10.0,
    ) -> None:
        """Initialize optimizer weights and parameters.

        Weights must be non-negative and sum to approximately 1.0.
        """
        assert alpha >= 0 and beta >= 0 and gamma >= 0, "Weights must be non-negative"
        total = alpha + beta + gamma
        assert abs(total - 1.0) < 1e-3, f"Weights must sum to 1.0, got {total}"

        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.enforce_water_budget = enforce_water_budget
        self.time_limit_seconds = time_limit_seconds

    @property
    def name(self) -> str:
        return "AquaGrid CP-SAT Optimizer"

    def _run(
        self,
        sites: list[DatacenterSite],
        profiles: dict[str, SiteEnvironmentalProfile],
        workloads: list[Workload],
    ) -> ScheduleResult:
        model = cp_model.CpModel()

        # Precompute per-hour execution metrics for every possible (job, site, hour)
        # to use in constraints and objective function.
        precomputed: dict[tuple[str, str, int], HourlyExecution] = {}
        for job in workloads:
            for site in sites:
                profile = profiles.get(site.id)
                if profile is None:
                    continue
                for h in range(job.arrival_hour, min(job.deadline_hour, 24)):
                    cond = profile.get_hour(h)
                    precomputed[(job.id, site.id, h)] = calculate_hourly_execution(
                        site=site,
                        workload_id=job.id,
                        gpus_used=job.gpus_required,
                        hour=h,
                        condition=cond,
                    )

        # -----------------------------------------------------------------
        # STEP 1: Decision Variables
        # -----------------------------------------------------------------
        # x[j, s, t] == 1 if job j executes at site s during hour t
        x: dict[tuple[str, str, int], cp_model.IntVar] = {}
        # y[j, s] == 1 if job j is assigned to site s
        y: dict[tuple[str, str], cp_model.IntVar] = {}

        for job in workloads:
            for site in sites:
                y[(job.id, site.id)] = model.new_bool_var(f"y_{job.id}_{site.id}")
                for h in range(job.arrival_hour, min(job.deadline_hour, 24)):
                    x[(job.id, site.id, h)] = model.new_bool_var(
                        f"x_{job.id}_{site.id}_{h}"
                    )

        # -----------------------------------------------------------------
        # STEP 2: Hard Constraints
        # -----------------------------------------------------------------

        # Rule 1: Single-Site Assignment & Total Compute Duration
        for job in workloads:
            # Must be placed at exactly one site
            model.add(sum(y[(job.id, site.id)] for site in sites) == 1)

            for site in sites:
                job_site_hours = [
                    x[(job.id, site.id, h)]
                    for h in range(job.arrival_hour, min(job.deadline_hour, 24))
                ]
                # If assigned to this site, sum of hours must equal duration; else 0
                model.add(sum(job_site_hours) == job.duration_hours * y[(job.id, site.id)])

        # Rule 2: Contiguous execution for non-preemptible jobs
        for job in workloads:
            if not job.is_preemptible:
                for site in sites:
                    # Define start-hour indicator: start_var[h] == 1 if job starts at hour h
                    latest_start = job.deadline_hour - job.duration_hours
                    start_vars = []
                    for start_h in range(job.arrival_hour, latest_start + 1):
                        if start_h + job.duration_hours > 24:
                            break
                        s_var = model.new_bool_var(f"start_{job.id}_{site.id}_{start_h}")
                        start_vars.append((start_h, s_var))

                    # Exactly one start hour if job is at this site; 0 otherwise
                    model.add(sum(s_var for _, s_var in start_vars) == y[(job.id, site.id)])

                    # Link each hour h to the start hours that cover it
                    for h in range(job.arrival_hour, min(job.deadline_hour, 24)):
                        covering_starts = [
                            s_var
                            for start_h, s_var in start_vars
                            if start_h <= h < start_h + job.duration_hours
                        ]
                        model.add(x[(job.id, site.id, h)] == sum(covering_starts))

        # Rule 3: GPU Capacity constraint at every site and hour
        for site in sites:
            for h in range(24):
                active_gpus = []
                for job in workloads:
                    if (job.id, site.id, h) in x:
                        active_gpus.append(x[(job.id, site.id, h)] * job.gpus_required)
                if active_gpus:
                    model.add(sum(active_gpus) <= site.gpu_capacity)

        # Rule 4: Local Water Budget Constraint (in Milliliters for exact integer math)
        if self.enforce_water_budget:
            for site in sites:
                water_terms = []
                for job in workloads:
                    for h in range(job.arrival_hour, min(job.deadline_hour, 24)):
                        if (job.id, site.id, h) in x:
                            calc = precomputed[(job.id, site.id, h)]
                            # Convert direct water liters to milliliters integer
                            direct_water_ml = int(round(calc.direct_water_liters * 1000.0))
                            water_terms.append(x[(job.id, site.id, h)] * direct_water_ml)

                if water_terms:
                    budget_ml = int(round(site.daily_water_budget_liters * 1000.0))
                    model.add(sum(water_terms) <= budget_ml)

        # -----------------------------------------------------------------
        # STEP 3: Multi-Objective Function (Scaled Integer Formulation)
        # -----------------------------------------------------------------
        # Cost: cents ($0.01)
        # Carbon: grams (g CO2)
        # Water: deciliters (0.1 L = 100 mL) to align metric scales
        w_cost = int(round(self.alpha * 1000.0))
        w_carbon = int(round(self.beta * 1000.0))
        w_water = int(round(self.gamma * 1000.0))

        objective_terms = []
        for job in workloads:
            for site in sites:
                for h in range(job.arrival_hour, min(job.deadline_hour, 24)):
                    if (job.id, site.id, h) in x:
                        calc = precomputed[(job.id, site.id, h)]
                        cost_cents = int(round(calc.cost_usd * 100.0))
                        carbon_g = int(round(calc.carbon_kg * 1000.0))
                        total_water_dl = int(
                            round((calc.direct_water_liters + calc.indirect_water_liters) * 10.0)
                        )

                        slice_score = (
                            w_cost * cost_cents
                            + w_carbon * carbon_g
                            + w_water * total_water_dl
                        )
                        objective_terms.append(x[(job.id, site.id, h)] * slice_score)

        model.minimize(sum(objective_terms))

        # -----------------------------------------------------------------
        # STEP 4: Solve the Model
        # -----------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit_seconds
        solver.parameters.num_workers = 4  # Parallel search workers

        status_code = solver.solve(model)

        # -----------------------------------------------------------------
        # STEP 5: Translate CP-SAT Output to ScheduleResult
        # -----------------------------------------------------------------
        all_executions: list[HourlyExecution] = []
        workload_schedules: list[WorkloadSchedule] = []

        if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            status_str = "OPTIMAL" if status_code == cp_model.OPTIMAL else "FEASIBLE"

            for job in workloads:
                assigned_site = None
                for site in sites:
                    if solver.value(y[(job.id, site.id)]) == 1:
                        assigned_site = site.id
                        break

                allocated_hours = [
                    h
                    for h in range(job.arrival_hour, min(job.deadline_hour, 24))
                    if solver.value(x[(job.id, assigned_site, h)]) == 1
                ]

                # Collect executions
                for h in allocated_hours:
                    all_executions.append(precomputed[(job.id, assigned_site, h)])

                start_h = min(allocated_hours) if allocated_hours else None
                finish_h = max(allocated_hours) + 1 if allocated_hours else None
                deadline_met = finish_h is not None and finish_h <= job.deadline_hour

                workload_schedules.append(
                    WorkloadSchedule(
                        workload_id=job.id,
                        scheduled=True,
                        site_id=assigned_site,
                        start_hour=start_h,
                        finish_hour=finish_h,
                        allocated_hours=allocated_hours,
                        deadline_met=deadline_met,
                        rejection_reason=None,
                    )
                )

            metrics = self._aggregate_metrics(all_executions, workload_schedules, sites)
            return ScheduleResult(
                scheduler_name=self.name,
                status=status_str,
                executions=all_executions,
                workload_schedules=workload_schedules,
                metrics=metrics,
                solve_time_seconds=0.0,
                notes=f"CP-SAT solved with status {status_str} (alpha={self.alpha}, beta={self.beta}, gamma={self.gamma})",
            )

        else:
            # INFEASIBLE or MODEL_INVALID
            workload_schedules = [
                WorkloadSchedule(
                    workload_id=j.id,
                    scheduled=False,
                    deadline_met=False,
                    rejection_reason="No feasible schedule exists that respects all constraints (GPU capacity, deadlines, or water budget).",
                )
                for j in workloads
            ]
            return ScheduleResult(
                scheduler_name=self.name,
                status="INFEASIBLE",
                executions=[],
                workload_schedules=workload_schedules,
                metrics=self._aggregate_metrics([], workload_schedules, sites),
                solve_time_seconds=0.0,
                notes=f"CP-SAT reported {solver.status_name(status_code)}",
            )
