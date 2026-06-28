"use client";

import { useState, useEffect, useCallback } from "react";
import { BarChart2, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import PageHeader from "@/components/layout/PageHeader";
import FilterPanel, { SelectFilter } from "@/components/ui/FilterPanel";
import DataTable, { type Column } from "@/components/ui/DataTable";
import StatCard from "@/components/ui/StatCard";
import type { WellRanking } from "@/lib/types";
import { fetchWellRankings } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

const COLUMNS: Column<WellRanking>[] = [
  {
    key: "rank",
    header: "#",
    sortable: true,
    render: (r) => (
      <span className={`inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
        r.rank === 1 ? "bg-amber-400 text-white"
        : r.rank === 2 ? "bg-slate-300 text-slate-800"
        : r.rank === 3 ? "bg-amber-700 text-white"
        : "bg-slate-100 text-slate-600"
      }`}>
        {r.rank}
      </span>
    ),
  },
  { key: "uwi",    header: "UWI",    sortable: true, render: (r) => r.well.uwi },
  { key: "strm",   header: "STRM",   sortable: false, render: (r) => r.well.strm },
  { key: "area",   header: "Area",   sortable: false, render: (r) => r.well.area },
  { key: "status", header: "Status", sortable: false, render: (r) => r.well.well_status_group },
  {
    key: "score",
    header: "Score",
    sortable: true,
    render: (r) => (
      <div className="flex items-center gap-2">
        <div className="flex-1 max-w-[80px] h-2 rounded-full bg-slate-100 overflow-hidden">
          <div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(100, r.score * 100)}%` }} />
        </div>
        <span className="text-xs font-medium text-slate-600">{r.score.toFixed(3)}</span>
      </div>
    ),
  },
  {
    key: "available_volume_m3",
    header: "Volume (m3)",
    sortable: true,
    render: (r) => r.well.available_volume_m3.toFixed(3),
  },
  {
    key: "burst_pressure_psi",
    header: "Burst Press. (psi)",
    sortable: true,
    render: (r) => r.well.burst_pressure_psi > 0 ? formatNumber(Math.round(r.well.burst_pressure_psi)) : "—",
  },
  { key: "volume_rank",   header: "Vol. Rank",   sortable: true, render: (r) => String(r.volume_rank) },
  { key: "pressure_rank", header: "Press. Rank", sortable: true, render: (r) => String(r.pressure_rank) },
];

const LIMIT_OPTIONS = [
  { value: "25",  label: "Top 25"  },
  { value: "50",  label: "Top 50"  },
  { value: "100", label: "Top 100" },
];

export default function WellRankingPage() {
  const [rankings, setRankings] = useState<WellRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState("50");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchWellRankings({ limit: parseInt(limit) });
      setRankings(data);
    } catch {
      setRankings([]);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => { load(); }, [load]);

  const chartData = rankings.slice(0, 15).map((r) => ({
    name: r.well.strm,
    score: parseFloat(r.score.toFixed(3)),
    volume: r.well.available_volume_m3,
  }));

  const top = rankings[0];

  return (
    <div>
      <PageHeader title="Well Ranking" description="Wells ranked by available volume and burst pressure" />

      <div className="flex gap-4">
        <div className="w-56 shrink-0 space-y-4">
          <FilterPanel>
            <SelectFilter label="Show" value={limit} onChange={setLimit} options={LIMIT_OPTIONS} />
          </FilterPanel>

          {top && (
            <div className="space-y-3">
              <StatCard label="Top Score"  value={top.score.toFixed(3)} icon={TrendingUp} />
              <StatCard label="Top UWI"    value={top.well.strm} />
              <StatCard label="Top Volume" value={`${top.well.available_volume_m3.toFixed(2)} m3`} icon={BarChart2} />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0 space-y-4">
          {chartData.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">Top 15 Wells by Score</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ left: 0, right: 10, top: 0, bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} angle={-40} textAnchor="end" interval={0} />
                  <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                  <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                  <Bar dataKey="score" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <DataTable
            columns={COLUMNS}
            data={rankings}
            keyField="rank"
            loading={loading}
            emptyMessage="No rankings available."
          />
        </div>
      </div>
    </div>
  );
}
