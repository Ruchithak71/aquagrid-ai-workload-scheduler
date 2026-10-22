"""Pydantic request and response schemas for the AquaGrid REST API."""

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
