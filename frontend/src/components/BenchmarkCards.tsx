import React from "react";
import { Cloud, Droplets, DollarSign, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";
import type { BenchmarkReport, SchedulerComparisonRow } from "../types";

interface BenchmarkCardsProps {
  report: BenchmarkReport;
  activePreset: string;
}

export const BenchmarkCards: React.FC<BenchmarkCardsProps> = ({ report, activePreset }) => {
  const getRow = (name: string): SchedulerComparisonRow | undefined => {
    return report.comparison_table.find((r) => r.scheduler_name.includes(name));
  };

  const fifo = getRow("FIFO");
  const carbonOnly = getRow("Carbon-Only");

  // Pick corresponding CP-SAT based on active preset
  const presetMap: Record<string, string> = {
    balanced: "CP-SAT (Balanced)",
    water_first: "CP-SAT (Water-First)",
    carbon_first: "CP-SAT (Carbon-First)",
    cost_first: "CP-SAT (Cost-First)",
  };
  const cpsatName = presetMap[activePreset] || "CP-SAT (Balanced)";
  const cpsat = getRow(cpsatName);

  const cards = [
    {
      title: "1. Naive FIFO",
      subtitle: "Status Quo (Queue-based)",
      badge: "Baseline 1",
      badgeColor: "bg-gray-800 text-gray-300 border-gray-700",
      accentBorder: "border-gray-800 hover:border-gray-700",
      accentBg: "from-gray-900 to-[#121622]",
      data: fifo,
    },
    {
      title: "2. Carbon-Only",
      subtitle: "Industry Standard (Grid-Aware)",
      badge: "Baseline 2",
      badgeColor: "bg-amber-950/80 text-amber-300 border-amber-800",
      accentBorder: "border-amber-900/50 hover:border-amber-700",
      accentBg: "from-amber-950/20 to-[#121622]",
      data: carbonOnly,
    },
    {
      title: "3. AquaGrid CP-SAT",
      subtitle: `Multi-Objective (${activePreset.toUpperCase()})`,
      badge: "Optimal",
      badgeColor: "bg-cyan-950 text-cyan-300 border-cyan-800 font-bold",
      accentBorder: "border-cyan-500/50 hover:border-cyan-400 shadow-lg shadow-cyan-500/10",
      accentBg: "from-cyan-950/30 to-[#121622]",
      data: cpsat,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
      {cards.map((card, idx) => {
        const d = card.data;
        if (!d) return null;

        const isCompliant = d.is_budget_compliant;

        return (
          <div
            key={idx}
            className={`rounded-2xl border p-5 bg-gradient-to-b ${card.accentBg} ${card.accentBorder} flex flex-col justify-between transition-all`}
          >
            {/* Header */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${card.badgeColor}`}>
                  {card.badge}
                </span>
                <span className="text-[11px] text-gray-400 flex items-center gap-1">
                  <Clock className="h-3 w-3" /> {d.solve_time_seconds.toFixed(3)}s
                </span>
              </div>
              <h3 className="text-lg font-bold text-white tracking-tight">{card.title}</h3>
              <p className="text-xs text-gray-400 mb-4">{card.subtitle}</p>

              {/* Water Budget Compliance Banner */}
              <div
                className={`mb-4 px-3 py-2 rounded-xl text-xs flex items-center gap-2 border ${
                  isCompliant
                    ? "bg-emerald-950/50 text-emerald-300 border-emerald-800"
                    : "bg-rose-950/70 text-rose-300 border-rose-800 animate-pulse"
                }`}
              >
                {isCompliant ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <span>100% Water Budget Compliant (0L violation)</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 text-rose-400 flex-shrink-0" />
                    <span className="font-semibold">
                      Violates Budget: +{d.water_budget_violations_liters.toFixed(1)}L over limit!
                    </span>
                  </>
                )}
              </div>

              {/* Metric Grid */}
              <div className="space-y-3">
                {/* Carbon */}
                <div className="flex items-center justify-between bg-black/30 p-2.5 rounded-xl border border-gray-800/80">
                  <div className="flex items-center gap-2 text-xs text-gray-300">
                    <Cloud className="h-4 w-4 text-emerald-400" />
                    <span>Carbon Emissions</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-white">{d.total_carbon_kg.toFixed(1)} kg</div>
                    {d.carbon_savings_pct_vs_fifo > 0 && (
                      <div className="text-[10px] text-emerald-400 font-semibold">
                        -{d.carbon_savings_pct_vs_fifo.toFixed(1)}% vs FIFO
                      </div>
                    )}
                  </div>
                </div>

                {/* Total Water */}
                <div className="flex items-center justify-between bg-black/30 p-2.5 rounded-xl border border-gray-800/80">
                  <div className="flex items-center gap-2 text-xs text-gray-300">
                    <Droplets className="h-4 w-4 text-cyan-400" />
                    <span>Total Water Consumed</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-white">{d.total_water_liters.toFixed(1)} L</div>
                    <div className="text-[10px] text-gray-400">
                      Direct: {d.total_direct_water_liters.toFixed(1)} L
                    </div>
                  </div>
                </div>

                {/* Electricity Cost */}
                <div className="flex items-center justify-between bg-black/30 p-2.5 rounded-xl border border-gray-800/80">
                  <div className="flex items-center gap-2 text-xs text-gray-300">
                    <DollarSign className="h-4 w-4 text-amber-400" />
                    <span>Electricity Cost</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-white">${d.total_cost_usd.toFixed(2)}</div>
                    <div className="text-[10px] text-gray-400">
                      {d.total_facility_energy_kwh.toFixed(1)} kWh total
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer status */}
            <div className="mt-4 pt-3 border-t border-gray-800/60 flex items-center justify-between text-[11px] text-gray-400">
              <span>Status: <strong className="text-gray-200">{d.status}</strong></span>
              <span>Jobs Placed: <strong className="text-gray-200">{d.jobs_scheduled}/5</strong></span>
            </div>
          </div>
        );
      })}
    </div>
  );
};
