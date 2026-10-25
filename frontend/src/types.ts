/**
 * TypeScript data models mirroring AquaGrid backend Pydantic schemas.
 */

export interface DatacenterSite {
  id: string;
  name: string;
  location: string;
  gpu_capacity: number;
  base_pue: number;
  pue_temp_slope: number;
  base_wue: number;
  wue_temp_slope: number;
  daily_water_budget_liters: number;
  cooling_type: string;
  economizer_temp_c: number;
}

export interface HourlyCondition {
  hour: number;
  temperature_c: number;
  carbon_intensity_g_per_kwh: number;
  electricity_price_per_kwh: number;
  grid_water_intensity_l_per_kwh: number;
}

export interface SiteEnvironmentalProfile {
  site_id: string;
  hourly_conditions: HourlyCondition[];
}

export interface Workload {
  id: string;
  name: string;
  arrival_hour: number;
  duration_hours: number;
  gpus_required: number;
  deadline_hour: number;
  priority: number;
  is_preemptible: boolean;
}

export interface SchedulerComparisonRow {
  scheduler_name: string;
  preset: string | null;
  status: string;
  jobs_scheduled: number;
  jobs_unscheduled: number;
  total_carbon_kg: number;
  total_water_liters: number;
  total_direct_water_liters: number;
  total_cost_usd: number;
  total_facility_energy_kwh: number;
  water_budget_violations_liters: number;
  is_budget_compliant: boolean;
  carbon_savings_pct_vs_fifo: number;
  water_savings_pct_vs_carbon_only: number;
  solve_time_seconds: number;
}

export interface HourlyExecution {
  workload_id: string;
  site_id: string;
  hour: number;
  gpus_used: number;
  it_energy_kwh: number;
  total_energy_kwh: number;
  direct_water_liters: number;
  indirect_water_liters: number;
  carbon_kg: number;
  cost_usd: number;
}

export interface WorkloadSchedule {
  workload_id: string;
  scheduled: boolean;
  site_id: string | null;
  start_hour: number | null;
  finish_hour: number | null;
  allocated_hours: number[];
  deadline_met: boolean;
  rejection_reason: string | null;
}

export interface ScheduleResult {
  scheduler_name: string;
  status: string;
  executions: HourlyExecution[];
  workload_schedules: WorkloadSchedule[];
  metrics: {
    total_it_energy_kwh: number;
    total_facility_energy_kwh: number;
    total_direct_water_liters: number;
    total_indirect_water_liters: number;
    total_water_liters: number;
    total_carbon_kg: number;
    total_cost_usd: number;
    jobs_scheduled: number;
    jobs_unscheduled: number;
    deadline_violations: number;
    water_budget_violations_liters: number;
    site_water_consumption: Record<string, number>;
  };
  solve_time_seconds: number;
  notes: string;
}

export interface BenchmarkReport {
  feasibility: {
    is_feasible: boolean;
    summary: string;
    network_utilization_pct: number;
  };
  comparison_table: SchedulerComparisonRow[];
  key_findings: string[];
  winner_for_carbon: string;
  winner_for_water: string;
  winner_for_cost: string;
  raw_results: Record<string, ScheduleResult>;
}

export interface BenchmarkRunSummary {
  id: number;
  created_at: string;
  name: string;
  enforce_water_budget: boolean;
  total_jobs: number;
  winner_carbon: string | null;
  winner_water: string | null;
  winner_cost: string | null;
  fifo_carbon_kg: number | null;
  cpsat_carbon_kg: number | null;
  carbon_reduction_pct: number | null;
  water_violations_avoided_liters: number | null;
}
