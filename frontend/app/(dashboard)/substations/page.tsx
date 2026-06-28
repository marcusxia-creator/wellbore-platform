"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { Zap, Map, Table2 } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import FilterPanel, { SelectFilter, SearchInput } from "@/components/ui/FilterPanel";
import DataTable, { type Column } from "@/components/ui/DataTable";
import StatCard from "@/components/ui/StatCard";
import type { Substation, SubstationFilters, MapMarker } from "@/lib/types";
import { fetchSubstations, fetchSubstationFilterOptions } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

const WellMap = dynamic(() => import("@/components/maps/WellMap"), { ssr: false });

const COLUMNS: Column<Substation>[] = [
  { key: "facility_code", header: "Code",         sortable: true  },
  { key: "name",          header: "Name",         sortable: true  },
  { key: "land_location", header: "Land Location",sortable: true  },
  { key: "area",          header: "Area",         sortable: true  },
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

type ViewMode = "split" | "map" | "table";

export default function SubstationsPage() {
  const [substations, setSubstations] = useState<Substation[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [viewMode, setViewMode] = useState<ViewMode>("split");

  const [search, setSearch] = useState("");
  const [area, setArea] = useState("");
  const [areaOptions, setAreaOptions] = useState<{ value: string; label: string }[]>([]);

  useEffect(() => {
    fetchSubstationFilterOptions()
      .then((opts) => setAreaOptions(opts.areas))
      .catch(() => setAreaOptions([
        { value: "AB", label: "AB" },
        { value: "SK", label: "SK" },
        { value: "BC", label: "BC" },
      ]));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const filters: SubstationFilters = {
        ...(search && { search }),
        ...(area   && { area }),
      };
      const res = await fetchSubstations(filters, 1, 1000);
      setSubstations(res.results);
      setTotal(res.count);
    } catch {
      setSubstations([]);
    } finally {
      setLoading(false);
    }
  }, [search, area]);

  useEffect(() => {
    const t = setTimeout(load, 400);
    return () => clearTimeout(t);
  }, [load]);

  const reset = () => { setSearch(""); setArea(""); };

  const markers: MapMarker[] = substations.map((s) => ({ type: "substation", data: s }));
  const withCapacity = substations.filter((s) => s.capacity_mw != null).length;

  return (
    <div>
      <PageHeader
        title="Substations"
        description={`Showing ${substations.length.toLocaleString()} of ${total.toLocaleString()} substations`}
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
                {v === "map" ? <Map size={13} /> : v === "table" ? <Table2 size={13} /> : <Zap size={13} />}
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Substations" value={formatNumber(total)} icon={Zap} />
        <StatCard label="Loaded" value={formatNumber(substations.length)} />
        <StatCard label="With Capacity" value={formatNumber(withCapacity)} />
        <StatCard label="Areas" value={areaOptions.length} />
      </div>

      <div className="flex gap-4">
        <div className="w-56 shrink-0">
          <FilterPanel onReset={reset}>
            <SearchInput value={search} onChange={setSearch} placeholder="Code or name..." />
            <SelectFilter label="Area" value={area} onChange={setArea} options={areaOptions} />
          </FilterPanel>
        </div>

        <div className="flex-1 min-w-0 space-y-4">
          {viewMode !== "table" && (
            <WellMap markers={markers} center={[53.5, -115.0]} zoom={5} height="420px" />
          )}
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
    </div>
  );
}
