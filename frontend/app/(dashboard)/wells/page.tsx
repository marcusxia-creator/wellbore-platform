"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import FilterPanel, {
  SearchInput,
  RadioFilter,
  SelectFilter,
  MultiSelectFilter,
} from "@/components/ui/FilterPanel";
import { formatNumber } from "@/lib/utils";
import type { ApiWell, FilterOption, MapMarker, Well } from "@/lib/types";
import {
  fetchWellsForMap,
  fetchWellStatuses,
  fetchWellTypes,
  fetchProductionInjectionFormations,
  MAP_WELL_LIMIT,
} from "@/lib/wells-backend";

const WellMap = dynamic(() => import("@/components/maps/WellMap"), { ssr: false });

const MAP_STYLE_OPTIONS = [
  { value: "basic", label: "Basic" },
  { value: "osm", label: "Street" },
  { value: "satellite", label: "Satellite" },
];

const STATUS_ALL = "ALL";

export default function WellsPage() {
  // ── Filters ────────────────────────────────────────────────────────────────
  const [tileStyle, setTileStyle] = useState("basic");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState(STATUS_ALL);
  const [wellType, setWellType] = useState("");
  const [formations, setFormations] = useState<(string | number)[]>([]);

  // ── Filter options (loaded from the backend metadata endpoints) ─────────────
  const [statusOptions, setStatusOptions] = useState<FilterOption[]>([]);
  const [typeOptions, setTypeOptions] = useState<FilterOption[]>([]);
  const [formationOptions, setFormationOptions] = useState<string[]>([]);

  // ── Data ────────────────────────────────────────────────────────────────────
  const [wells, setWells] = useState<ApiWell[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const reqId = useRef(0);

  // Debounce the search box.
  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  // Load dropdown options once.
  useEffect(() => {
    fetchWellStatuses().then(setStatusOptions).catch(() => {});
    fetchWellTypes().then(setTypeOptions).catch(() => {});
    fetchProductionInjectionFormations()
      .then((opts) => setFormationOptions(opts.map((o) => o.value)))
      .catch(() => {});
  }, []);

  // Fetch the map sample whenever a filter changes (server-side filtering).
  useEffect(() => {
    const id = ++reqId.current;
    setLoading(true);
    fetchWellsForMap({
      search: search || undefined,
      status: status !== STATUS_ALL ? status : undefined,
      well_type: wellType || undefined,
      prod_inject_frmtn: formations.length ? formations.map(String) : undefined,
    })
      .then(({ wells, total }) => {
        if (id !== reqId.current) return;
        setWells(wells);
        setTotal(total);
      })
      .catch(() => {
        if (id !== reqId.current) return;
        setWells([]);
        setTotal(0);
      })
      .finally(() => {
        if (id === reqId.current) setLoading(false);
      });
  }, [search, status, wellType, formations]);

  // ── Derived ──────────────────────────────────────────────────────────────────
  const plotted = useMemo(
    () => wells.filter((w) => w.latitude != null && w.longitude != null),
    [wells]
  );

  const markers = useMemo<MapMarker[]>(
    () =>
      plotted.map((w) => ({
        type: "well" as const,
        // WellMap reads a small subset of fields via a lat/long + status shape.
        data: {
          id: w.id,
          uwi: w.uwi,
          name: w.name,
          latitude: w.latitude,
          longitude: w.longitude,
          well_status_group: w.status,
        } as unknown as Well,
      })),
    [plotted]
  );

  const activeCount = useMemo(
    () => wells.filter((w) => w.status === "Active").length,
    [wells]
  );

  const capped = total > wells.length;

  const reset = () => {
    setSearchInput("");
    setSearch("");
    setStatus(STATUS_ALL);
    setWellType("");
    setFormations([]);
  };

  return (
    <div className="flex gap-4">
      {/* Filter sidebar */}
      <div className="w-56 shrink-0">
        <FilterPanel onReset={reset} className="overflow-y-auto max-h-[calc(100vh-6rem)]">
          <SearchInput
            value={searchInput}
            onChange={setSearchInput}
            placeholder="Search UWI, name, operator…"
          />
          <RadioFilter
            label="Well Status"
            value={status}
            onChange={setStatus}
            options={[{ value: STATUS_ALL, label: "ALL" }, ...statusOptions]}
          />
          <SelectFilter
            label="Well Type"
            value={wellType}
            onChange={setWellType}
            options={typeOptions}
          />
          <MultiSelectFilter
            label="Formation"
            values={formations}
            onChange={setFormations}
            options={formationOptions}
          />
          <RadioFilter
            label="Map Style"
            value={tileStyle}
            onChange={setTileStyle}
            options={MAP_STYLE_OPTIONS}
          />
        </FilterPanel>
      </div>

      {/* Right column: KPIs + map */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">
        {/* KPI cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Matching Wells</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(total)}
            </p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Shown on Map</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(plotted.length)}
            </p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Active (sample)</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(activeCount)}
            </p>
          </div>
        </div>

        {/* Capped-sample notice */}
        {!loading && capped && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">
            Showing a sample of {formatNumber(wells.length)} of {formatNumber(total)} matching
            wells (map is capped at {formatNumber(MAP_WELL_LIMIT)}). Narrow the filters to see a
            more specific set.
          </div>
        )}

        <WellMap
          markers={markers}
          center={[53.5, -115.0]}
          zoom={6}
          height="calc(100vh - 16rem)"
          tileStyle={tileStyle}
        />

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-slate-500 px-1">
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500" />
            Active
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-slate-500" />
            Inactive
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-amber-400" />
            Suspended
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-500" />
            ABD
          </span>
        </div>
      </div>
    </div>
  );
}
