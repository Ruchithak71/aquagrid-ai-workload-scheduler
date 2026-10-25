/**
 * HTTP client for communicating with the AquaGrid FastAPI backend.
 */

import type {
  DatacenterSite,
  SiteEnvironmentalProfile,
  Workload,
  BenchmarkReport,
  BenchmarkRunSummary,
} from "../types";

const API_BASE =
  import.meta.env.VITE_API_URL ||
  (typeof window !== "undefined" && window.location.port === "5173"
    ? "http://localhost:8000/api"
    : "/api");

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function fetchSites(): Promise<DatacenterSite[]> {
  const res = await fetch(`${API_BASE}/sites`);
  if (!res.ok) throw new Error("Failed to load datacenters");
  return res.json();
}

export async function fetchEnvironmentalProfile(siteId: string): Promise<SiteEnvironmentalProfile> {
  const res = await fetch(`${API_BASE}/sites/${siteId}/environmental`);
  if (!res.ok) throw new Error(`Failed to load profile for ${siteId}`);
  return res.json();
}

export async function fetchWorkloads(): Promise<Workload[]> {
  const res = await fetch(`${API_BASE}/workloads`);
  if (!res.ok) throw new Error("Failed to load canonical workloads");
  return res.json();
}

export async function runBenchmarkComparison(params: {
  enforce_water_budget: boolean;
  save_to_history?: boolean;
  run_name?: string;
}): Promise<BenchmarkReport> {
  const res = await fetch(`${API_BASE}/schedule/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      enforce_water_budget: params.enforce_water_budget,
      save_to_history: params.save_to_history ?? false,
      run_name: params.run_name ?? "Dashboard Benchmark Comparison",
    }),
  });
  if (!res.ok) throw new Error("Optimization benchmark failed");
  return res.json();
}

export async function fetchHistory(): Promise<BenchmarkRunSummary[]> {
  const res = await fetch(`${API_BASE}/history`);
  if (!res.ok) throw new Error("Failed to load history");
  return res.json();
}

export async function fetchHistoryDetail(id: number): Promise<{ report: BenchmarkReport }> {
  const res = await fetch(`${API_BASE}/history/${id}`);
  if (!res.ok) throw new Error(`Failed to load historical run #${id}`);
  return res.json();
}

export async function deleteHistoryRun(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/history/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete run #${id}`);
}
