import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { ThermometerSun } from "lucide-react";
import type { SiteEnvironmentalProfile } from "../types";

interface TelemetryViewProps {
  phoenixProfile: SiteEnvironmentalProfile | null;
}

export const TelemetryView: React.FC<TelemetryViewProps> = ({ phoenixProfile }) => {
  if (!phoenixProfile) return null;

  const data = phoenixProfile.hourly_conditions.map((c) => ({
    hour: `${c.hour}:00`,
    temp: c.temperature_c,
    carbon: c.carbon_intensity_g_per_kwh,
    price: c.electricity_price_per_kwh,
  }));

  return (
    <div className="bg-[#111726] border border-gray-800 rounded-2xl p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <ThermometerSun className="h-4 w-4 text-orange-400" />
            <h4 className="text-sm font-bold text-white">
              Phoenix, AZ: 24-Hour Solar vs. Heat Telemetry Curve
            </h4>
          </div>
          <p className="text-xs text-gray-400">
            Notice how Peak Solar (Hours 11-15: low 35g carbon) collides with 42°C heat and peak electricity rates!
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-orange-400">
            <span className="h-2.5 w-2.5 rounded-full bg-orange-500 inline-block" />
            <span>Temp (°C)</span>
          </div>
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 inline-block" />
            <span>Carbon (g/kWh)</span>
          </div>
          <div className="flex items-center gap-1.5 text-amber-400">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500 inline-block" />
            <span>Price ($/kWh × 100)</span>
          </div>
        </div>
      </div>

      <div className="h-60 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorCarbon" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
            <XAxis dataKey="hour" stroke="#64748b" tick={{ fontSize: 10 }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }}
              formatter={(val: any, name: any) => {
                if (name === "temp") return [`${Number(val).toFixed(1)} °C`, "Ambient Heat"];
                if (name === "carbon") return [`${Number(val).toFixed(0)} gCO₂/kWh`, "Grid Carbon"];
                return [`$${(Number(val) * 100).toFixed(1)} cents`, "Price"];
              }}
            />
            <Area type="monotone" dataKey="temp" stroke="#f97316" fillOpacity={1} fill="url(#colorTemp)" />
            <Area type="monotone" dataKey="carbon" stroke="#10b981" fillOpacity={1} fill="url(#colorCarbon)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
