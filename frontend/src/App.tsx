import React, { useEffect, useState } from "react";
import { Header } from "./components/Header";
import { WeightController } from "./components/WeightController";
import { BenchmarkCards } from "./components/BenchmarkCards";
import { ComparisonCharts } from "./components/ComparisonCharts";
import { TelemetryView } from "./components/TelemetryView";
import { GanttTimeline } from "./components/GanttTimeline";
import { HistoryDrawer } from "./components/HistoryDrawer";
import {
  checkBackendHealth,
  fetchSites,
  fetchEnvironmentalProfile,
  fetchWorkloads,
  runBenchmarkComparison,
  fetchHistory,
  fetchHistoryDetail,
  deleteHistoryRun,
} from "./services/api";
import type {
  DatacenterSite,
  SiteEnvironmentalProfile,
  Workload,
  BenchmarkReport,
  BenchmarkRunSummary,
} from "./types";
import { History, AlertCircle } from "lucide-react";

export const App: React.FC = () => {
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [sites, setSites] = useState<DatacenterSite[]>([]);
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [phoenixProfile, setPhoenixProfile] = useState<SiteEnvironmentalProfile | null>(null);

  const [activePreset, setActivePreset] = useState<string>("balanced");
  const [enforceWaterBudget, setEnforceWaterBudget] = useState<boolean>(true);
  const [saveToHistory, setSaveToHistory] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [historyList, setHistoryList] = useState<BenchmarkRunSummary[]>([]);
  const [historyOpen, setHistoryOpen] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Initialize data on mount
  useEffect(() => {
    async function init() {
      const isOnline = await checkBackendHealth();
      setBackendOnline(isOnline);

      if (isOnline) {
        try {
          const [loadedSites, loadedWorkloads, profile, hist] = await Promise.all([
            fetchSites(),
            fetchWorkloads(),
            fetchEnvironmentalProfile("phoenix-01"),
            fetchHistory(),
          ]);

          setSites(loadedSites);
          setWorkloads(loadedWorkloads);
          setPhoenixProfile(profile);
          setHistoryList(hist);

          // Run initial benchmark comparison
          setLoading(true);
          const initialReport = await runBenchmarkComparison({
            enforce_water_budget: true,
            save_to_history: false,
          });
          setReport(initialReport);
        } catch (err: any) {
          setErrorMsg(err.message || "Failed to load initial data");
        } finally {
          setLoading(false);
        }
      }
    }

    init();
  }, []);

  const handleRunComparison = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await runBenchmarkComparison({
        enforce_water_budget: enforceWaterBudget,
        save_to_history: saveToHistory,
        run_name: `Benchmark Run (${activePreset.toUpperCase()})`,
      });
      setReport(res);

      if (saveToHistory) {
        const updatedHist = await fetchHistory();
        setHistoryList(updatedHist);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Benchmark failed");
    } finally {
      setLoading(false);
    }
  };

  const handleLoadHistoricalRun = async (id: number) => {
    try {
      setLoading(true);
      const detail = await fetchHistoryDetail(id);
      setReport(detail.report);
      setHistoryOpen(false);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load historical run");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteHistoricalRun = async (id: number) => {
    try {
      await deleteHistoryRun(id);
      setHistoryList((prev) => prev.filter((r) => r.id !== id));
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to delete run");
    }
  };

  // Determine current active schedule result for Gantt chart
  const presetMap: Record<string, string> = {
    balanced: "CP-SAT (Balanced)",
    water_first: "CP-SAT (Water-First)",
    carbon_first: "CP-SAT (Carbon-First)",
    cost_first: "CP-SAT (Cost-First)",
  };
  const activeSchedulerName = presetMap[activePreset] || "CP-SAT (Balanced)";
  const currentScheduleResult = report?.raw_results[activeSchedulerName] || null;

  return (
    <div className="min-h-screen bg-[#0b0f19] text-gray-100 flex flex-col font-sans">
      {/* Header */}
      <Header backendOnline={backendOnline} activePreset={activePreset} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Offline Banner */}
        {!backendOnline && (
          <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              <span>
                Backend server is currently offline. Start the backend with:{" "}
                <code className="bg-black/50 px-2 py-0.5 rounded font-mono text-white">
                  uvicorn src.api.main:app --reload --app-dir backend
                </code>
              </span>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3 rounded-xl bg-amber-950/50 border border-amber-800 text-amber-200 text-xs flex items-center justify-between">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="underline text-[11px]">
              Dismiss
            </button>
          </div>
        )}

        {/* Top Controls Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Optimization Control & Decision Support
            </h2>
            <p className="text-xs text-gray-400">
              Tune optimization weights or enforce regional water budgets across {sites.length || 3} distributed datacenters.
            </p>
          </div>

          <button
            onClick={() => setHistoryOpen(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 text-xs font-semibold self-start sm:self-auto transition-all"
          >
            <History className="h-4 w-4 text-indigo-400" />
            <span>Saved Runs ({historyList.length})</span>
          </button>
        </div>

        {/* Pareto Weight Controller */}
        <WeightController
          activePreset={activePreset}
          onSelectPreset={(p) => setActivePreset(p)}
          enforceWaterBudget={enforceWaterBudget}
          onToggleWaterBudget={(val) => setEnforceWaterBudget(val)}
          saveToHistory={saveToHistory}
          onToggleSaveHistory={(val) => setSaveToHistory(val)}
          onRunComparison={handleRunComparison}
          loading={loading}
        />

        {/* 3-Way KPI Cards */}
        {report && <BenchmarkCards report={report} activePreset={activePreset} />}

        {/* Comparison Charts */}
        {report && <ComparisonCharts report={report} />}

        {/* Telemetry View & Gantt Timeline */}
        <div className="grid grid-cols-1 gap-6">
          <TelemetryView phoenixProfile={phoenixProfile} />
          <GanttTimeline scheduleResult={currentScheduleResult} workloads={workloads} />
        </div>
      </main>

      {/* Experiment History Drawer */}
      <HistoryDrawer
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        historyList={historyList}
        onLoadRun={handleLoadHistoricalRun}
        onDeleteRun={handleDeleteHistoricalRun}
      />

      {/* Footer */}
      <footer className="border-t border-gray-900 bg-[#080b12] py-6 text-center text-xs text-gray-500">
        AquaGrid: AI Workload Scheduling with Water, Energy, and Carbon Awareness • Google OR-Tools CP-SAT + FastAPI + React
      </footer>
    </div>
  );
};

export default App;
