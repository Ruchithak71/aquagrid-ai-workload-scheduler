"""Execution records, schedule outputs, and aggregate metrics."""

from pydantic import BaseModel, Field


class HourlyExecution(BaseModel):
    """The physical resource consumption of a workload running at a site for 1 hour."""

    workload_id: str
    site_id: str
    hour: int
    gpus_used: int
    it_energy_kwh: float = Field(ge=0.0)
    total_energy_kwh: float = Field(ge=0.0)
    direct_water_liters: float = Field(ge=0.0)
    indirect_water_liters: float = Field(ge=0.0)
    carbon_kg: float = Field(ge=0.0)
    cost_usd: float = Field(ge=0.0)


class WorkloadSchedule(BaseModel):
    """Scheduling outcome for an individual AI workload."""

    workload_id: str
    scheduled: bool
    site_id: str | None = None
    start_hour: int | None = None
    finish_hour: int | None = None
    allocated_hours: list[int] = Field(default_factory=list)
    deadline_met: bool = True
    rejection_reason: str | None = None


class ScheduleMetrics(BaseModel):
    """System-wide aggregate performance and environmental metrics."""

    total_it_energy_kwh: float = Field(default=0.0, ge=0.0)
    total_facility_energy_kwh: float = Field(default=0.0, ge=0.0)
    total_direct_water_liters: float = Field(default=0.0, ge=0.0)
    total_indirect_water_liters: float = Field(default=0.0, ge=0.0)
    total_water_liters: float = Field(default=0.0, ge=0.0)
    total_carbon_kg: float = Field(default=0.0, ge=0.0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    jobs_scheduled: int = Field(default=0, ge=0)
    jobs_unscheduled: int = Field(default=0, ge=0)
    deadline_violations: int = Field(default=0, ge=0)
    water_budget_violations_liters: float = Field(default=0.0, ge=0.0)
    site_water_consumption: dict[str, float] = Field(default_factory=dict)


class ScheduleResult(BaseModel):
    """Complete outcome of a scheduling run across all sites and workloads."""

    scheduler_name: str
    status: str = Field(description="'OPTIMAL', 'FEASIBLE', 'INFEASIBLE', or 'ERROR'")
    executions: list[HourlyExecution] = Field(default_factory=list)
    workload_schedules: list[WorkloadSchedule] = Field(default_factory=list)
    metrics: ScheduleMetrics
    solve_time_seconds: float = Field(ge=0.0)
    notes: str = ""
