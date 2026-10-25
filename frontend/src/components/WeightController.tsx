import React from "react";
import { Sliders, ShieldCheck, Play, RefreshCw, BookmarkCheck } from "lucide-react";

interface WeightControllerProps {
  activePreset: string;
  onSelectPreset: (preset: string) => void;
  enforceWaterBudget: boolean;
  onToggleWaterBudget: (val: boolean) => void;
  saveToHistory: boolean;
  onToggleSaveHistory: (val: boolean) => void;
  onRunComparison: () => void;
  loading: boolean;
}

export const WeightController: React.FC<WeightControllerProps> = ({
  activePreset,
  onSelectPreset,
  enforceWaterBudget,
  onToggleWaterBudget,
  saveToHistory,
  onToggleSaveHistory,
  onRunComparison,
  loading,
}) => {
  const presets = [
    {
      id: "balanced",
      label: "Balanced",
      weights: "33% Cost • 33% Carbon • 34% Water",
      color: "from-blue-600 to-cyan-600",
    },
    {
      id: "water_first",
      label: "Water-First",
      weights: "10% Cost • 10% Carbon • 80% Water",
      color: "from-cyan-600 to-teal-600",
    },
    {
      id: "carbon_first",
      label: "Carbon-First",
      weights: "10% Cost • 80% Carbon • 10% Water",
      color: "from-emerald-600 to-green-600",
    },
    {
      id: "cost_first",
      label: "Cost-First",
      weights: "80% Cost • 10% Carbon • 10% Water",
      color: "from-amber-600 to-orange-600",
    },
  ];

  return (
    <div className="bg-[#111726] border border-gray-800 rounded-2xl p-5 shadow-xl">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Preset Selector */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-sm font-semibold text-gray-200">
            <Sliders className="h-4 w-4 text-cyan-400" />
            <span>Optimization Priority Presets</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {presets.map((p) => {
              const active = activePreset === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => onSelectPreset(p.id)}
                  className={`px-3 py-2 rounded-xl text-left transition-all border ${
                    active
                      ? "bg-gradient-to-r text-white border-cyan-500/50 shadow-md " + p.color
                      : "bg-gray-900/80 text-gray-400 border-gray-800 hover:border-gray-700 hover:text-gray-200"
                  }`}
                >
                  <div className="text-xs font-bold">{p.label}</div>
                  <div className="text-[10px] opacity-80 mt-0.5 truncate">{p.weights}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Toggles & CTA */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2 lg:pt-0">
          {/* Water Budget Toggle */}
          <label className="flex items-center space-x-2.5 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={enforceWaterBudget}
              onChange={(e) => onToggleWaterBudget(e.target.checked)}
              className="rounded bg-gray-800 border-gray-700 text-cyan-500 focus:ring-cyan-500 h-4 w-4"
            />
            <div className="text-xs">
              <span className="font-semibold text-gray-200 flex items-center gap-1">
                <ShieldCheck className="h-3.5 w-3.5 text-cyan-400 inline" /> Enforce Water Budget
              </span>
              <p className="text-[10px] text-gray-400">Hard constraint on Phoenix (400L)</p>
            </div>
          </label>

          {/* Save to History Toggle */}
          <label className="flex items-center space-x-2.5 px-3 py-2 rounded-xl bg-gray-900 border border-gray-800 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={saveToHistory}
              onChange={(e) => onToggleSaveHistory(e.target.checked)}
              className="rounded bg-gray-800 border-gray-700 text-indigo-500 focus:ring-indigo-500 h-4 w-4"
            />
            <div className="text-xs">
              <span className="font-semibold text-gray-200 flex items-center gap-1">
                <BookmarkCheck className="h-3.5 w-3.5 text-indigo-400 inline" /> Save to DB
              </span>
              <p className="text-[10px] text-gray-400">Persist to experiment history</p>
            </div>
          </label>

          {/* Run Benchmark Button */}
          <button
            onClick={onRunComparison}
            disabled={loading}
            className="flex items-center justify-center space-x-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:via-blue-500 hover:to-indigo-500 text-white font-bold text-sm shadow-lg shadow-cyan-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Solving CP-SAT...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-white" />
                <span>Run 6-Way Benchmark</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
