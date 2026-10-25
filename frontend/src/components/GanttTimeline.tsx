import React from "react";
import { Calendar, Cpu } from "lucide-react";
import type { ScheduleResult, Workload } from "../types";

interface GanttTimelineProps {
  scheduleResult: ScheduleResult | null;
  workloads: Workload[];
}

export const GanttTimeline: React.FC<GanttTimelineProps> = ({ scheduleResult, workloads }) => {
  if (!scheduleResult || scheduleResult.workload_schedules.length === 0) return null;

  const hours = Array.from({ length: 24 }, (_, i) => i);

  const siteColors: Record<string, string> = {
    "phoenix-01": "bg-amber-600/80 border-amber-500 text-amber-100",
    "quincy-01": "bg-cyan-600/80 border-cyan-500 text-cyan-100",
    "council-bluffs-01": "bg-indigo-600/80 border-indigo-500 text-indigo-100",
  };

  const siteNames: Record<string, string> = {
    "phoenix-01": "Phoenix (AZ)",
    "quincy-01": "Quincy (WA)",
    "council-bluffs-01": "Council Bluffs (IA)",
  };

  return (
    <div className="bg-[#111726] border border-gray-800 rounded-2xl p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-cyan-400" />
            <h4 className="text-sm font-bold text-white">
              Spatial-Temporal Schedule Timeline ({scheduleResult.scheduler_name})
            </h4>
          </div>
          <p className="text-xs text-gray-400">
            24-hour GPU execution grid. Colored blocks represent active hours at chosen datacenters.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          {Object.entries(siteColors).map(([siteId, colorClass]) => (
            <div key={siteId} className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded border ${colorClass} inline-block`} />
              <span className="text-gray-300">{siteNames[siteId]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Grid Container */}
      <div className="overflow-x-auto">
        <div className="min-w-[700px]">
          {/* Hour Header */}
          <div
            className="gap-1 mb-2 text-[10px] text-gray-500 font-mono text-center"
            style={{ display: "grid", gridTemplateColumns: "180px repeat(24, minmax(0, 1fr))" }}
          >
            <div className="text-left font-sans text-gray-400">Workload</div>
            {hours.map((h) => (
              <div key={h} className="border-l border-gray-800/80 pl-0.5">
                {h}h
              </div>
            ))}
          </div>

          {/* Rows */}
          <div className="space-y-2">
            {scheduleResult.workload_schedules.map((ws) => {
              const job = workloads.find((w) => w.id === ws.workload_id);
              const jobName = job?.name || ws.workload_id;
              const gpus = job?.gpus_required || 0;
              const siteId = ws.site_id || "";
              const colorClass = siteColors[siteId] || "bg-gray-700 border-gray-600";

              return (
                <div
                  key={ws.workload_id}
                  className="gap-1 items-center"
                  style={{ display: "grid", gridTemplateColumns: "180px repeat(24, minmax(0, 1fr))" }}
                >
                  {/* Job Label */}
                  <div className="truncate text-xs text-gray-300 pr-2 flex items-center gap-1">
                    <Cpu className="h-3 w-3 text-gray-500 flex-shrink-0" />
                    <span className="truncate font-medium">{jobName}</span>
                    <span className="text-[10px] text-gray-500">({gpus}g)</span>
                  </div>

                  {/* 24 Hour Slots */}
                  {hours.map((h) => {
                    const isActive = ws.allocated_hours.includes(h);
                    const isWithinWindow =
                      job && h >= job.arrival_hour && h <= job.deadline_hour;

                    return (
                      <div
                        key={h}
                        className={`h-6 rounded-md flex items-center justify-center text-[10px] transition-all ${
                          isActive
                            ? `${colorClass} border font-bold shadow-sm`
                            : isWithinWindow
                            ? "bg-gray-900/60 border border-gray-800/50"
                            : "bg-black/20"
                        }`}
                        title={
                          isActive
                            ? `${jobName} running at ${siteNames[siteId]} (${h}:00)`
                            : isWithinWindow
                            ? "Eligible window"
                            : "Outside window"
                        }
                      >
                        {isActive ? "" : ""}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
