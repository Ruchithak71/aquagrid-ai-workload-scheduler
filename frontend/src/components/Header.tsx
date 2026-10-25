import React from "react";
import { Droplets, Cpu, Activity, Server, Zap } from "lucide-react";

interface HeaderProps {
  backendOnline: boolean;
  activePreset: string;
}

export const Header: React.FC<HeaderProps> = ({ backendOnline, activePreset }) => {
  return (
    <header className="border-b border-gray-800 bg-[#0d1322]/90 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Brand & Title */}
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Droplets className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">AquaGrid</h1>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                v1.0 • CP-SAT Engine
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Multi-Objective AI Workload & Regional Water-Aware Scheduler
            </p>
          </div>
        </div>

        {/* Live System Badges */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* API Health Pill */}
          <div
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-full border ${
              backendOnline
                ? "bg-emerald-950/60 text-emerald-400 border-emerald-800"
                : "bg-rose-950/60 text-rose-400 border-rose-800 animate-pulse"
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            <span>{backendOnline ? "API Connected (Port 8000)" : "Backend Offline"}</span>
          </div>

          {/* Infrastructure Specs */}
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-gray-900 text-gray-300 border border-gray-800">
            <Server className="h-3.5 w-3.5 text-cyan-400" />
            <span>3 Regions (AZ, WA, IA)</span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-gray-900 text-gray-300 border border-gray-800">
            <Cpu className="h-3.5 w-3.5 text-indigo-400" />
            <span>352 H100 GPUs</span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-gray-900 text-gray-300 border border-gray-800">
            <Zap className="h-3.5 w-3.5 text-amber-400" />
            <span>Active: {activePreset.toUpperCase()}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
