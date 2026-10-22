"""Workload scheduling, benchmark comparison, and feasibility diagnostic routes."""

from fastapi import APIRouter, HTTPException

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
def compare_schedulers_endpoint(request: CompareRequest) -> BenchmarkReport:
    """Run full 6-model benchmark comparison across identical scenario inputs."""
    sites = request.sites or get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = request.workloads or get_default_workloads()

    return compare_schedulers(
        sites=sites,
        profiles=profiles,
        workloads=workloads,
        enforce_water_budget=request.enforce_water_budget,
    )


@router.post("/diagnose", response_model=FeasibilityReport)
def diagnose_scenario_endpoint(request: DiagnoseRequest) -> FeasibilityReport:
    """Run pre-flight feasibility checks to identify bottlenecks or capacity deficits."""
    sites = request.sites or get_default_sites()
    profiles = get_default_environmental_profiles()
    workloads = request.workloads or get_default_workloads()

    return diagnose_scenario(sites=sites, profiles=profiles, workloads=workloads)
