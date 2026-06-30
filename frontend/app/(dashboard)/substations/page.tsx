"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Map, Table2, Zap } from "lucide-react";
import FilterPanel, { RadioFilter, SelectFilter, SearchInput } from "@/components/ui/FilterPanel";
import DataTable, { type Column } from "@/components/ui/DataTable";
import type { Substation } from "@/lib/types";
import { formatNumber } from "@/lib/utils";
import { useSubstations, type ViewMode } from "./useSubstations";
import { MAP_STYLE_OPTIONS } from "../wells/constants";

const WellMap = dynamic(() => import("@/components/maps/WellMap"), { ssr: false });

const COLUMNS: Column<Substation>[] = [
  { key: "facility_code", header: "Code",          sortable: true  },
  { key: "name",          header: "Name",          sortable: true  },
  { key: "land_location", header: "Land Location", sortable: true  },
  { key: "area",          header: "Area",          sortable: true  },
  {
    key: "township",
    header: "Twp-Rge-Mer",
    sortable: false,
    render: (r) => `${r.township}-${r.range}W${r.meridian}`,
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
    key: "capacity_mw",
    header: "Capacity (MW)",
    sortable: true,
    render: (r) => r.capacity_mw != null ? formatNumber(r.capacity_mw) : "—",
  },
  { key: "address", header: "Address", sortable: false },
];

const VIEW_OPTIONS: { value: ViewMode; label: string; icon: React.ReactNode }[] = [
  { value: "split", label: "Split", icon: <Zap    size={13} /> },
  { value: "map",   label: "Map",   icon: <Map    size={13} /> },
  { value: "table", label: "Table", icon: <Table2 size={13} /> },
];

export default function SubstationsPage() {
  const {
    substations, loading, total, viewMode,
    search, area, areaOptions,
    setViewMode, setSearch, setArea, reset,
    markers, withCapacity,
  } = useSubstations();

  const [tileStyle, setTileStyle] = useState("basic");

  return (
    <div className="flex gap-4">

      {/* Filter sidebar */}
      <div className="w-56 shrink-0">
        <FilterPanel onReset={reset} className="overflow-y-auto max-h-[calc(100vh-6rem)]">
          <RadioFilter label="Map Style" value={tileStyle} onChange={setTileStyle} options={MAP_STYLE_OPTIONS} />
          <SearchInput value={search} onChange={setSearch} placeholder="Code or name…" />
          <SelectFilter label="Area" value={area} onChange={setArea} options={areaOptions} />
        </FilterPanel>
      </div>

      {/* Right column */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">

        {/* KPI cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Total Substations</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(total)}
            </p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Loaded</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(substations.length)}
            </p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">With Capacity</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(withCapacity)}
            </p>
          </div>
        </div>

        {/* View toggle */}
        <div className="flex gap-1 self-start rounded-lg border border-slate-200 bg-white p-1">
          {VIEW_OPTIONS.map(({ value, label, icon }) => (
            <button
              key={value}
              onClick={() => setViewMode(value)}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                viewMode === value
                  ? "bg-emerald-600 text-white"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {icon}{label}
            </button>
          ))}
        </div>

        {/* Map */}
        {viewMode !== "table" && (
          <WellMap
            markers={markers}
            center={[53.5, -115.0]}
            zoom={5}
            height={viewMode === "map" ? "calc(100vh - 18rem)" : "420px"}
            tileStyle={tileStyle}
          />
        )}

        {/* Table */}
        {viewMode !== "map" && (
          <DataTable
            columns={COLUMNS}
            data={substations}
            keyField="id"
            loading={loading}
            emptyMessage="No substations match the current filters."
          />
        )}
      </div>
    </div>
  );
}
