import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Sparkles, BarChart3 } from "lucide-react";
import type { BenchmarkReport } from "../types";

interface ComparisonChartsProps {
  report: BenchmarkReport;
}

export const ComparisonCharts: React.FC<ComparisonChartsProps> = ({ report }) => {
  const data = report.comparison_table.map((row) => ({
    name: row.scheduler_name.replace("CP-SAT ", ""),
    carbon: row.total_carbon_kg,
    water: row.total_water_liters,
    isCompliant: row.is_budget_compliant,
  }));

  const carbonColors: Record<string, string> = {
    FIFO: "#ef4444",
    "Carbon-Only": "#f59e0b",
    "(Balanced)": "#06b6d4",
    "(Water-First)": "#0284c7",
    "(Carbon-First)": "#10b981",
    "(Cost-First)": "#8b5cf6",
  };

  const waterColors: Record<string, string> = {
    FIFO: "#64748b",
    "Carbon-Only": "#dc2626", // Red because it violated water budget!
    "(Balanced)": "#06b6d4",
    "(Water-First)": "#0284c7",
    "(Carbon-First)": "#10b981",
    "(Cost-First)": "#8b5cf6",
  };

  return (
    <div className="space-y-5">
      {/* Automated Key Findings Banner */}
      {report.key_findings.length > 0 && (
        <div className="bg-gradient-to-r from-blue-950/40 via-cyan-950/30 to-indigo-950/40 border border-cyan-800/50 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center space-x-2 text-sm font-bold text-cyan-300 mb-2">
            <Sparkles className="h-4 w-4" />
            <span>Automated Optimization Findings & Trade-Off Analysis</span>
          </div>
          <ul className="space-y-1.5 text-xs text-gray-300">
            {report.key_findings.map((f, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Dual Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Carbon Chart */}
        <div className="bg-[#111726] border border-gray-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4 text-emerald-400" />
              <h4 className="text-sm font-bold text-white">Carbon Emissions by Scheduler (kg CO₂)</h4>
            </div>
            <span className="text-[10px] text-gray-400 font-mono">Lower is better</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} interval={0} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }}
                  formatter={(value: any) => [`${Number(value).toFixed(1)} kg`, "Carbon"]}
                />
                <Bar dataKey="carbon" radius={[6, 6, 0, 0]}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={carbonColors[entry.name] || "#3b82f6"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Water Chart */}
        <div className="bg-[#111726] border border-gray-800 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4 text-cyan-400" />
              <h4 className="text-sm font-bold text-white">Total Water Consumed (Liters)</h4>
            </div>
            <span className="text-[10px] text-rose-400 font-mono">Red bar = Water Budget Violated</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} interval={0} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }}
                  formatter={(value: any) => [`${Number(value).toFixed(1)} L`, "Total Water"]}
                />
                <Bar dataKey="water" radius={[6, 6, 0, 0]}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={waterColors[entry.name] || "#06b6d4"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
