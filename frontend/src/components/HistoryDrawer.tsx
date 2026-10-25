import React from "react";
import { History, Trash2, ArrowUpRight, X } from "lucide-react";
import type { BenchmarkRunSummary } from "../types";

interface HistoryDrawerProps {
  open: boolean;
  onClose: () => void;
  historyList: BenchmarkRunSummary[];
  onLoadRun: (id: number) => void;
  onDeleteRun: (id: number) => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  open,
  onClose,
  historyList,
  onLoadRun,
  onDeleteRun,
}) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-md bg-[#0f1422] border-l border-gray-800 h-full p-6 flex flex-col justify-between shadow-2xl">
        {/* Header */}
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-gray-800">
            <div className="flex items-center space-x-2 text-white font-bold">
              <History className="h-5 w-5 text-indigo-400" />
              <span>Experiment History (Database)</span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <p className="text-xs text-gray-400 mt-2 mb-4">
            Reload or inspect previously saved benchmark comparisons from SQLite / PostgreSQL.
          </p>

          {/* List */}
          <div className="space-y-3 overflow-y-auto max-h-[calc(100vh-180px)] pr-1">
            {historyList.length === 0 ? (
              <div className="text-center py-12 text-xs text-gray-500">
                No saved benchmark runs yet. Check "Save to DB" on the main dashboard to persist runs.
              </div>
            ) : (
              historyList.map((item) => (
                <div
                  key={item.id}
                  className="bg-gray-900/80 border border-gray-800 rounded-xl p-3.5 hover:border-gray-700 transition-all flex flex-col justify-between gap-2"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h5 className="text-sm font-semibold text-white">{item.name}</h5>
                      <p className="text-[10px] text-gray-400 font-mono">
                        {new Date(item.created_at).toLocaleString()} • ID #{item.id}
                      </p>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                      -{item.carbon_reduction_pct?.toFixed(1) || 0}% Carbon
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-800/60">
                    <span className="text-[11px] text-gray-400">
                      Winner: <strong className="text-cyan-400">{item.winner_carbon || "CP-SAT"}</strong>
                    </span>

                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => onLoadRun(item.id)}
                        className="px-2.5 py-1 rounded-lg bg-indigo-900/60 hover:bg-indigo-800 text-indigo-300 text-xs flex items-center gap-1 border border-indigo-700/50"
                      >
                        <span>Load</span>
                        <ArrowUpRight className="h-3 w-3" />
                      </button>

                      <button
                        onClick={() => onDeleteRun(item.id)}
                        className="p-1 rounded-lg text-gray-500 hover:text-rose-400 hover:bg-rose-950/30"
                        title="Delete run"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-gray-800 text-[11px] text-gray-500 text-center">
          Persisted via SQLAlchemy 2.0 ORM
        </div>
      </div>
    </div>
  );
};
