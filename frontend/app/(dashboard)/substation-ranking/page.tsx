"use client";

import { useState, useEffect, useCallback } from "react";
import { Award, Zap } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import PageHeader from "@/components/layout/PageHeader";
import FilterPanel, { SelectFilter } from "@/components/ui/FilterPanel";
import DataTable, { type Column } from "@/components/ui/DataTable";
import StatCard from "@/components/ui/StatCard";
import type { SubstationRanking } from "@/lib/types";
import { fetchSubstationRankings } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

const COLUMNS: Column<SubstationRanking>[] = [
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
  { key: "code",     header: "Code",     sortable: false, render: (r) => r.substation.facility_code },
  { key: "name",     header: "Name",     sortable: true,  render: (r) => r.substation.name },
  { key: "area",     header: "Area",     sortable: false, render: (r) => r.substation.area },
  { key: "location", header: "Location", sortable: false, render: (r) => r.substation.land_location },
  {
    key: "capacity_mw",
    header: "Capacity (MW)",
    sortable: false,
    render: (r) => r.substation.capacity_mw != null ? formatNumber(r.substation.capacity_mw) : "—",
  },
  {
    key: "score",
    header: "Score",
    sortable: true,
    render: (r) => (
      <div className="flex items-center gap-2">
        <div className="flex-1 max-w-[80px] h-2 rounded-full bg-slate-100 overflow-hidden">
          <div className="h-full rounded-full bg-violet-500" style={{ width: `${Math.min(100, r.score * 100)}%` }} />
        </div>
        <span className="text-xs font-medium text-slate-600">{r.score.toFixed(4)}</span>
      </div>
    ),
  },
  {
    key: "nearby_wells",
    header: "Wells Nearby",
    sortable: true,
    render: (r) => formatNumber(r.substation.nearby_well_count),
  },
  {
    key: "well_density",
    header: "Well Density",
    sortable: true,
    render: (r) => r.well_density.toFixed(3),
  },
];

const AREA_OPTIONS = [
  { value: "AB", label: "AB" },
  { value: "SK", label: "SK" },
  { value: "BC", label: "BC" },
];

const LIMIT_OPTIONS = [
  { value: "25",  label: "Top 25"  },
  { value: "50",  label: "Top 50"  },
  { value: "100", label: "Top 100" },
];

export default function SubstationRankingPage() {
  const [rankings, setRankings] = useState<SubstationRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [area, setArea] = useState("");
  const [limit, setLimit] = useState("50");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSubstationRankings({
        ...(area && { area }),
        limit: parseInt(limit),
      });
      setRankings(data);
    } catch {
      setRankings([]);
    } finally {
      setLoading(false);
    }
  }, [area, limit]);

  useEffect(() => { load(); }, [load]);

  const chartData = rankings.slice(0, 15).map((r) => ({
    name: r.substation.name.length > 14 ? r.substation.name.slice(0, 12) + "..." : r.substation.name,
    score: parseFloat(r.score.toFixed(4)),
    wells: r.substation.nearby_well_count,
  }));

  const top = rankings[0];

  return (
    <div>
      <PageHeader title="Substation Ranking" description="Substations scored by nearby well density" />

      <div className="flex gap-4">
        <div className="w-56 shrink-0 space-y-4">
          <FilterPanel>
            <SelectFilter label="Area" value={area} onChange={setArea} options={AREA_OPTIONS} />
            <SelectFilter label="Show" value={limit} onChange={setLimit} options={LIMIT_OPTIONS} />
          </FilterPanel>

          {top && (
            <div className="space-y-3">
              <StatCard label="Top Score"      value={top.score.toFixed(4)} icon={Award} />
              <StatCard label="Top Substation" value={top.substation.name}  icon={Zap}   />
              <StatCard label="Wells Nearby"   value={top.substation.nearby_well_count} />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0 space-y-4">
          {loading && (
            <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-400">
              Computing rankings from {limit} substations — this may take a moment...
            </div>
          )}
          {!loading && chartData.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">Top 15 Substations by Score</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ left: 0, right: 10, top: 0, bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} angle={-40} textAnchor="end" interval={0} />
                  <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
                  <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }} />
                  <Bar dataKey="score" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          <DataTable
            columns={COLUMNS}
            data={rankings}
            keyField="rank"
            loading={loading}
            emptyMessage="No substation rankings available."
          />
        </div>
      </div>
    </div>
  );
}
