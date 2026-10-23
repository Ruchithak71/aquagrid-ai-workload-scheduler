"""Workload scheduling, benchmark comparison, and feasibility diagnostic routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.models import ScheduleResult
from src.api.schemas import RunScheduleRequest, CompareRequest, DiagnoseRequest
from src.scheduling.fifo import FIFOScheduler
from src.scheduling.carbon_only import CarbonOnlyScheduler
from src.scheduling.cpsat import CPSATScheduler
from src.scheduling.pareto import OptimizationPreset, get_preset_scheduler, run_preset
from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)
from src.simulation.comparator import BenchmarkReport, compare_schedulers
from src.simulation.diagnoser import FeasibilityReport, diagnose_scenario
from src.db.session import get_db
from src.db.models import BenchmarkRunRecord

router = APIRouter(prefix="/schedule", tags=["Scheduling"])


@router.post("/run", response_model=ScheduleResult)
def run_scheduler_endpoint(request: RunScheduleRequest) -> ScheduleResult:
    """Execute a single scheduler (FIFO, Carbon-Only, or CP-SAT) with chosen parameters."""
    sites = request.sites or get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = request.workloads or get_default_workloads()

    scheduler_type = request.scheduler_type.lower()

    if scheduler_type == "fifo":
        scheduler = FIFOScheduler()
    elif scheduler_type == "carbon_only":
        scheduler = CarbonOnlyScheduler()
    elif scheduler_type == "cpsat":
        if request.preset:
            try:
                preset_enum = OptimizationPreset(request.preset.lower())
                return run_preset(
                    preset=preset_enum,
                    sites=sites,
                    profiles=profiles,
                    workloads=workloads,
                    enforce_water_budget=request.enforce_water_budget,
                )
            except ValueError:
                valid = [p.value for p in OptimizationPreset]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid preset '{request.preset}'. Must be one of: {valid}",
                )
        elif request.alpha is not None and request.beta is not None and request.gamma is not None:
            try:
                scheduler = CPSATScheduler(
                    alpha=request.alpha,
                    beta=request.beta,
                    gamma=request.gamma,
                    enforce_water_budget=request.enforce_water_budget,
                )
            except AssertionError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            scheduler = CPSATScheduler(enforce_water_budget=request.enforce_water_budget)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scheduler_type '{request.scheduler_type}'. Must be 'fifo', 'carbon_only', or 'cpsat'.",
        )

    return scheduler.schedule(sites, profiles, workloads)


@router.post("/compare", response_model=BenchmarkReport)
def compare_schedulers_endpoint(
    request: CompareRequest,
    db: Session = Depends(get_db),
) -> BenchmarkReport:
    """Run full 6-model benchmark comparison across identical scenario inputs."""
    sites = request.sites or get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = request.workloads or get_default_workloads()

    report = compare_schedulers(
        sites=sites,
        profiles=profiles,
        workloads=workloads,
        enforce_water_budget=request.enforce_water_budget,
    )

    if request.save_to_history:
        fifo_row = next((r for r in report.comparison_table if r.scheduler_name == "FIFO"), None)
        cpsat_row = next((r for r in report.comparison_table if r.scheduler_name == "CP-SAT (Balanced)"), None)
        co_row = next((r for r in report.comparison_table if r.scheduler_name == "Carbon-Only"), None)

        record = BenchmarkRunRecord(
            name=request.run_name,
            enforce_water_budget=request.enforce_water_budget,
            total_jobs=len(workloads),
            winner_carbon=report.winner_for_carbon,
            winner_water=report.winner_for_water,
            winner_cost=report.winner_for_cost,
            fifo_carbon_kg=fifo_row.total_carbon_kg if fifo_row else None,
            cpsat_carbon_kg=cpsat_row.total_carbon_kg if cpsat_row else None,
            carbon_reduction_pct=cpsat_row.carbon_savings_pct_vs_fifo if cpsat_row else None,
            water_violations_avoided_liters=co_row.water_budget_violations_liters if co_row else None,
            report_json=report.model_dump_json(),
        )
        db.add(record)
        db.commit()

    return report


@router.post("/diagnose", response_model=FeasibilityReport)
def diagnose_scenario_endpoint(request: DiagnoseRequest) -> FeasibilityReport:
    """Run pre-flight feasibility checks to identify bottlenecks or capacity deficits."""
    sites = request.sites or get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = request.workloads or get_default_workloads()

    return diagnose_scenario(sites=sites, profiles=profiles, workloads=workloads)
