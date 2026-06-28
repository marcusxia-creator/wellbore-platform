"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Target, Search } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import FilterPanel, { SelectFilter } from "@/components/ui/FilterPanel";
import DataTable, { type Column } from "@/components/ui/DataTable";
import StatCard from "@/components/ui/StatCard";
import type { BestPoint } from "@/lib/types";
import type { MapMarker } from "@/lib/types";
import { fetchBestPoint } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

const WellMap = dynamic(() => import("@/components/maps/WellMap"), { ssr: false });

const COLUMNS: Column<BestPoint>[] = [
  {
    key: "score",
    header: "Score",
    sortable: true,
    render: (r) => (
      <span className="font-semibold text-emerald-700">{r.score.toFixed(3)}</span>
    ),
  },
  {
    key: "latitude",
    header: "Latitude",
    sortable: true,
    render: (r) => r.latitude.toFixed(5),
  },
  {
    key: "longitude",
    header: "Longitude",
    sortable: true,
    render: (r) => r.longitude.toFixed(5),
  },
  {
    key: "well_count",
    header: "Wells Nearby",
    sortable: true,
    render: (r) => formatNumber(r.well_count),
  },
  {
    key: "avg_volume_m3",
    header: "Avg Volume (m3)",
    sortable: true,
    render: (r) => formatNumber(r.avg_volume_m3, 0),
  },
];

const STATUS_OPTIONS = [
  { value: "IDLE", label: "IDLE (Active)" },
  { value: "SUSP", label: "SUSP (Suspended)" },
  { value: "ABD",  label: "ABD (Abandoned)" },
];

export default function BestPointPage() {
  const [north, setNorth] = useState("57.0");
  const [south, setSouth] = useState("49.5");
  const [east, setEast] = useState("-110.0");
  const [west, setWest] = useState("-120.0");
  const [radius, setRadius] = useState("100");
  const [minWells, setMinWells] = useState("3");
  const [status, setStatus] = useState("IDLE");

  const [results, setResults] = useState<BestPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  async function handleSearch() {
    setLoading(true);
    setSearched(true);
    setSelectedIdx(null);
    try {
      const data = await fetchBestPoint({
        search_area: {
          north: parseFloat(north),
          south: parseFloat(south),
          east: parseFloat(east),
          west: parseFloat(west),
        },
        radius_miles: parseFloat(radius) || 5,
        min_wells: parseInt(minWells) || 3,
        ...(status && { well_status_group: status }),
      });
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  const markers: MapMarker[] = results.map((bp) => ({ type: "bestPoint", data: bp }));
  const best = results[0];

  return (
    <div>
      <PageHeader
        title="Best Point"
        description="Find the optimal infrastructure location based on well density and production"
      />

      <div className="flex gap-4">
        <div className="w-56 shrink-0 space-y-4">
          <FilterPanel>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "North", value: north, set: setNorth },
                { label: "South", value: south, set: setSouth },
                { label: "East", value: east, set: setEast },
                { label: "West", value: west, set: setWest },
              ].map(({ label, value, set }) => (
                <div key={label} className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-slate-500">{label}</label>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => set(e.target.value)}
                    className="rounded-lg border border-slate-200 px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    step="0.1"
                  />
                </div>
              ))}
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-500">Radius (miles)</label>
              <input
                type="number"
                value={radius}
                onChange={(e) => setRadius(e.target.value)}
                min="1"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-500">Min Wells</label>
              <input
                type="number"
                value={minWells}
                onChange={(e) => setMinWells(e.target.value)}
                min="1"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <SelectFilter label="Well Status" value={status} onChange={setStatus} options={STATUS_OPTIONS} />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Search size={15} />
              {loading ? "Analyzing…" : "Find Best Point"}
            </button>
          </FilterPanel>

          {best && (
            <div className="space-y-3">
              <StatCard label="Best Score" value={best.score.toFixed(3)} icon={Target} />
              <StatCard label="Wells Nearby" value={best.well_count} />
              {best.avg_volume_m3 != null && (
                <StatCard label="Avg Production" value={`${formatNumber(best.avg_volume_m3)} m3`} />
              )}
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0 space-y-4">
          <WellMap markers={markers} height="420px" center={[53.5, -115.0]} zoom={5} />
          {searched && (
            <DataTable
              columns={COLUMNS}
              data={results}
              keyField="score"
              loading={loading}
              onRowClick={(row) => setSelectedIdx((row as BestPoint).score as unknown as number)}
              emptyMessage="No candidate points found. Try expanding the search area or lowering Min Wells."
                      />
          )}
        </div>
      </div>
    </div>
  );
}
