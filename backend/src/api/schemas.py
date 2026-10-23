"""Pydantic request and response schemas for the AquaGrid REST API."""

from datetime import datetime
from pydantic import BaseModel, Field

from src.models import DatacenterSite, Workload


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"
    service: str = "aquagrid-api"


class RunScheduleRequest(BaseModel):
    """Parameters for running an individual scheduling algorithm."""

    scheduler_type: str = Field(
        default="cpsat",
        description="One of: 'fifo', 'carbon_only', or 'cpsat'",
    )
    preset: str | None = Field(
        default=None,
        description="Optional CP-SAT preset: 'balanced', 'cost_first', 'carbon_first', or 'water_first'",
    )
    alpha: float | None = Field(default=None, ge=0.0, le=1.0, description="Cost weight")
    beta: float | None = Field(default=None, ge=0.0, le=1.0, description="Carbon weight")
    gamma: float | None = Field(default=None, ge=0.0, le=1.0, description="Water weight")
    enforce_water_budget: bool = Field(
        default=True,
        description="Whether to enforce local water budgets as hard constraints",
    )
    sites: list[DatacenterSite] | None = Field(
        default=None,
        description="Optional custom sites; defaults to canonical benchmark sites if omitted",
    )
    workloads: list[Workload] | None = Field(
        default=None,
        description="Optional custom workloads; defaults to canonical benchmark workloads if omitted",
    )


class CompareRequest(BaseModel):
    """Parameters for running the 6-way benchmark comparison."""

    sites: list[DatacenterSite] | None = Field(
        default=None,
        description="Optional custom sites; defaults to canonical benchmark sites if omitted",
    )
    workloads: list[Workload] | None = Field(
        default=None,
        description="Optional custom workloads; defaults to canonical benchmark workloads if omitted",
    )
    enforce_water_budget: bool = Field(
        default=True,
        description="Whether to enforce local water budgets in CP-SAT runs",
    )
    save_to_history: bool = Field(
        default=False,
        description="Whether to automatically persist this run to the database",
    )
    run_name: str = Field(
        default="Benchmark Comparison",
        description="Label for this benchmark run in history",
    )


class DiagnoseRequest(BaseModel):
    """Parameters for running pre-flight feasibility diagnostics."""

    sites: list[DatacenterSite] | None = Field(
        default=None,
        description="Optional custom sites; defaults to canonical benchmark sites if omitted",
    )
    workloads: list[Workload] | None = Field(
        default=None,
        description="Optional custom workloads; defaults to canonical benchmark workloads if omitted",
    )


class BenchmarkRunSummary(BaseModel):
    """Lightweight summary of a historical benchmark comparison."""

    id: int
    created_at: datetime
    name: str
    enforce_water_budget: bool
    total_jobs: int
    winner_carbon: str | None = None
    winner_water: str | None = None
    winner_cost: str | None = None
    fifo_carbon_kg: float | None = None
    cpsat_carbon_kg: float | None = None
    carbon_reduction_pct: float | None = None
    water_violations_avoided_liters: float | None = None


class BenchmarkRunDetail(BenchmarkRunSummary):
    """Full detail of a historical benchmark run, including the complete report."""

    report: dict

