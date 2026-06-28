"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { PlusCircle, Map, Table2 } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import FilterPanel, { SelectFilter } from "@/components/ui/FilterPanel";
import DataTable, { type Column } from "@/components/ui/DataTable";
import StatCard from "@/components/ui/StatCard";
import type { SubstationCandidate, MapMarker, BestPoint } from "@/lib/types";
import { fetchSubstationCandidates } from "@/lib/api";
import { formatNumber, formatDepth } from "@/lib/utils";

const WellMap = dynamic(() => import("@/components/maps/WellMap"), { ssr: false });

const COLUMNS: Column<SubstationCandidate>[] = [
  {
    key: "score",
    header: "Score",
    sortable: true,
    render: (r) => (
      <div className="flex items-center gap-2">
        <div className="flex-1 max-w-[80px] h-2 rounded-full bg-slate-100 overflow-hidden">
          <div
            className="h-full rounded-full bg-amber-500"
            style={{ width: `${Math.min(100, r.score * 100)}%` }}
          />
        </div>
        <span className="text-xs font-semibold text-amber-700">{r.score.toFixed(3)}</span>
      </div>
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
  { key: "county", header: "County", sortable: true },
  { key: "state", header: "State", sortable: true },
  {
    key: "nearby_well_count",
    header: "Nearby Wells",
    sortable: true,
    render: (r) => formatNumber(r.nearby_well_count),
  },
  {
    key: "avg_well_depth_ft",
    header: "Avg Well Depth",
    sortable: true,
    render: (r) => formatDepth(r.avg_well_depth_ft),
  },
  {
    key: "estimated_load_mva",
    header: "Est. Load (MVA)",
    sortable: true,
    render: (r) => r.estimated_load_mva.toFixed(1),
  },
];

const LIMIT_OPTIONS = [
  { value: "25", label: "Top 25" },
  { value: "50", label: "Top 50" },
  { value: "100", label: "Top 100" },
];

const MIN_WELLS_OPTIONS = [
  { value: "1", label: "≥ 1 well" },
  { value: "3", label: "≥ 3 wells" },
  { value: "5", label: "≥ 5 wells" },
  { value: "10", label: "≥ 10 wells" },
];

type ViewMode = "split" | "map" | "table";

export default function SubstationCandidatesPage() {
  const [candidates, setCandidates] = useState<SubstationCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("split");
  const [county, setCounty] = useState("");
  const [minWells, setMinWells] = useState("3");
  const [limit, setLimit] = useState("50");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSubstationCandidates({
        ...(county && { county }),
        min_wells: parseInt(minWells),
        limit: parseInt(limit),
      });
      setCandidates(data);
    } catch {
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }, [county, minWells, limit]);

  useEffect(() => { load(); }, [load]);

  const markers: MapMarker[] = candidates.map((c) => ({
    type: "bestPoint",
    data: {
      latitude: c.latitude,
      longitude: c.longitude,
      well_count: c.nearby_well_count,
      avg_volume_m3: null,
      score: c.score,
      nearby_wells: [],
    } as BestPoint,
  }));

  const best = candidates[0];
  const avgLoad =
    candidates.length > 0
      ? candidates.reduce((s, c) => s + c.estimated_load_mva, 0) / candidates.length
      : null;

  return (
    <div>
      <PageHeader
        title="Substation Candidates"
        description="Optimal candidate locations for new substation infrastructure"
        actions={
          <div className="flex gap-1 rounded-lg border border-slate-200 bg-white p-1">
            {(["split", "map", "table"] as ViewMode[]).map((v) => (
              <button
                key={v}
                onClick={() => setViewMode(v)}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  viewMode === v ? "bg-emerald-600 text-white" : "text-slate-500 hover:text-slate-800"
                }`}
              >
                {v === "map" ? <Map size={13} /> : v === "table" ? <Table2 size={13} /> : <PlusCircle size={13} />}
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Candidates" value={formatNumber(candidates.length)} icon={PlusCircle} />
        {best && <StatCard label="Top Score" value={best.score.toFixed(3)} />}
        {best && <StatCard label="Top Wells Nearby" value={best.nearby_well_count} />}
        {avgLoad != null && (
          <StatCard label="Avg Est. Load" value={`${avgLoad.toFixed(1)} MVA`} />
        )}
      </div>

      <div className="flex gap-4">
        <div className="w-56 shrink-0">
          <FilterPanel onReset={() => { setCounty(""); setMinWells("3"); setLimit("50"); }}>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-500">County</label>
              <input
                type="text"
                value={county}
                onChange={(e) => setCounty(e.target.value)}
                placeholder="Filter by county…"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <SelectFilter label="Min Nearby Wells" value={minWells} onChange={setMinWells} options={MIN_WELLS_OPTIONS} />
            <SelectFilter label="Show" value={limit} onChange={setLimit} options={LIMIT_OPTIONS} />
          </FilterPanel>
        </div>

        <div className="flex-1 min-w-0 space-y-4">
          {viewMode !== "table" && (
            <WellMap markers={markers} height="420px" />
          )}
          {viewMode !== "map" && (
            <DataTable
              columns={COLUMNS}
              data={candidates}
              keyField="id"
              loading={loading}
              emptyMessage="No candidate locations found."
            />
          )}
        </div>
      </div>
    </div>
  );
}
