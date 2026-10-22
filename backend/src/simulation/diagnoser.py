"""Pre-flight validation and Infeasibility Diagnoser for AquaGrid.

Inspects sites, environmental profiles, and submitted workloads to detect
mathematical impossibilities (e.g. GPU capacity deficit, invalid deadlines,
or water budget exhaustion) and provides human-readable diagnostic messages.
"""

from pydantic import BaseModel, Field

from src.models import DatacenterSite, SiteEnvironmentalProfile, Workload


class DiagnosticIssue(BaseModel):
    """An identified feasibility bottleneck or violation."""

    category: str = Field(description="'TIME_WINDOW', 'GPU_CAPACITY', 'NETWORK_OVERLOAD', or 'WATER_BUDGET'")
    severity: str = Field(description="'CRITICAL' (infeasible) or 'WARNING'")
    entity_id: str
    message: str


class FeasibilityReport(BaseModel):
    """Result of pre-flight feasibility analysis."""

    is_feasible: bool
    critical_issues: list[DiagnosticIssue] = Field(default_factory=list)
    warnings: list[DiagnosticIssue] = Field(default_factory=list)
    total_gpu_hours_demanded: int
    total_gpu_hours_available: int
    network_utilization_pct: float
    summary: str


def diagnose_scenario(
    sites: list[DatacenterSite],
    profiles: dict[str, SiteEnvironmentalProfile],
    workloads: list[Workload],
) -> FeasibilityReport:
    """Analyze scenario parameters and diagnose potential infeasibilities."""
    critical_issues: list[DiagnosticIssue] = []
    warnings: list[DiagnosticIssue] = []

    # 1. Total Network Compute Availability
    total_gpu_hours_available = sum(site.gpu_capacity * 24 for site in sites)
    total_gpu_hours_demanded = sum(w.gpus_required * w.duration_hours for w in workloads)

    utilization_pct = (
        round((total_gpu_hours_demanded / total_gpu_hours_available) * 100.0, 2)
        if total_gpu_hours_available > 0
        else 0.0
    )

    if total_gpu_hours_demanded > total_gpu_hours_available:
        critical_issues.append(
            DiagnosticIssue(
                category="NETWORK_OVERLOAD",
                severity="CRITICAL",
                entity_id="network",
                message=(
                    f"Total GPU-hours demanded ({total_gpu_hours_demanded} GPU-hrs) exceeds total "
                    f"network capacity ({total_gpu_hours_available} GPU-hrs across 24h)."
                ),
            )
        )
    elif utilization_pct > 85.0:
        warnings.append(
            DiagnosticIssue(
                category="NETWORK_OVERLOAD",
                severity="WARNING",
                entity_id="network",
                message=f"High network GPU utilization ({utilization_pct}%). Congestion likely.",
            )
        )

    # 2. Individual Workload Feasibility Checks
    max_site_gpus = max((s.gpu_capacity for s in sites), default=0)

    for job in workloads:
        # Check A: Single-site GPU capacity limit
        if job.gpus_required > max_site_gpus:
            critical_issues.append(
                DiagnosticIssue(
                    category="GPU_CAPACITY",
                    severity="CRITICAL",
                    entity_id=job.id,
                    message=(
                        f"Workload '{job.name}' ({job.id}) requires {job.gpus_required} GPUs, "
                        f"but the largest site in the network has only {max_site_gpus} GPUs."
                    ),
                )
            )

        # Check B: Time window duration sufficiency
        window = job.deadline_hour - job.arrival_hour
        if window < job.duration_hours:
            critical_issues.append(
                DiagnosticIssue(
                    category="TIME_WINDOW",
                    severity="CRITICAL",
                    entity_id=job.id,
                    message=(
                        f"Workload '{job.name}' ({job.id}) requires {job.duration_hours}h duration, "
                        f"but its window (arrival={job.arrival_hour}, deadline={job.deadline_hour}) "
                        f"is only {window}h."
                    ),
                )
            )

        # Check C: Zero scheduling slack warning
        elif window == job.duration_hours:
            warnings.append(
                DiagnosticIssue(
                    category="TIME_WINDOW",
                    severity="WARNING",
                    entity_id=job.id,
                    message=(
                        f"Workload '{job.name}' ({job.id}) has zero scheduling slack "
                        f"(duration equals deadline window). Must run immediately at arrival."
                    ),
                )
            )

    # 3. Water Budget Sanity Check
    total_water_budget = sum(s.daily_water_budget_liters for s in sites)
    if total_water_budget <= 0.0:
        critical_issues.append(
            DiagnosticIssue(
                category="WATER_BUDGET",
                severity="CRITICAL",
                entity_id="network_water",
                message="Total network water budget is zero or negative.",
            )
        )

    is_feasible = len(critical_issues) == 0

    if is_feasible:
        summary = (
            f"Scenario is feasible. Network utilization is {utilization_pct}% "
            f"({total_gpu_hours_demanded}/{total_gpu_hours_available} GPU-hrs)."
        )
    else:
        summary = (
            f"Scenario is INFEASIBLE: Found {len(critical_issues)} critical bottlenecks "
            f"preventing a valid schedule."
        )

    return FeasibilityReport(
        is_feasible=is_feasible,
        critical_issues=critical_issues,
        warnings=warnings,
        total_gpu_hours_demanded=total_gpu_hours_demanded,
        total_gpu_hours_available=total_gpu_hours_available,
        network_utilization_pct=utilization_pct,
        summary=summary,
    )
