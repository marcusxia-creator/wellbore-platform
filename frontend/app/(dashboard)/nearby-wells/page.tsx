"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { MapPin, Search } from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import FilterPanel, { SelectFilter } from "@/components/ui/FilterPanel";
import DataTable, { type Column } from "@/components/ui/DataTable";
import StatCard from "@/components/ui/StatCard";
import type { NearbyWellResult, MapMarker } from "@/lib/types";
import { fetchNearbyWells } from "@/lib/api";

const WellMap = dynamic(() => import("@/components/maps/WellMap"), { ssr: false });

const COLUMNS: Column<NearbyWellResult>[] = [
  { key: "uwi",               header: "UWI",            sortable: true  },
  { key: "strm",              header: "STRM",           sortable: true  },
  { key: "well_status_group", header: "Status",         sortable: true  },
  { key: "well_status_text",  header: "Status Text",    sortable: false },
  {
    key: "distance_miles",
    header: "Distance (mi)",
    sortable: true,
    render: (r) => r.distance_miles.toFixed(2),
  },
  {
    key: "available_volume_m3",
    header: "Volume (m3)",
    sortable: true,
    render: (r) => r.available_volume_m3.toFixed(3),
  },
  {
    key: "horizontal_hole",
    header: "Horizontal",
    sortable: true,
    render: (r) => r.horizontal_hole ? "Yes" : "No",
  },
  { key: "format", header: "Format", sortable: true },
];

const STATUS_OPTIONS = [
  { value: "IDLE", label: "IDLE (Active)" },
  { value: "SUSP", label: "SUSP (Suspended)" },
  { value: "ABD",  label: "ABD (Abandoned)" },
];

export default function NearbyWellsPage() {
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [radius, setRadius] = useState("50");
  const [statusGroup, setStatusGroup] = useState("");
  const [pinLat, setPinLat] = useState<number | null>(null);
  const [pinLng, setPinLng] = useState<number | null>(null);

  const [results, setResults] = useState<NearbyWellResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch() {
    if (!lat || !lng) return;
    setLoading(true);
    setSearched(true);
    const parsedLat = parseFloat(lat);
    const parsedLng = parseFloat(lng);
    setPinLat(parsedLat);
    setPinLng(parsedLng);
    try {
      const data = await fetchNearbyWells({
        latitude: parsedLat,
        longitude: parsedLng,
        radius_miles: parseFloat(radius) || 50,
        ...(statusGroup && { well_status_group: statusGroup }),
      });
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  function handleMapClick(clickLat: number, clickLng: number) {
    setLat(clickLat.toFixed(5));
    setLng(clickLng.toFixed(5));
  }

  const markers: MapMarker[] = [
    ...(pinLat != null && pinLng != null
      ? [{ type: "pin" as const, lat: pinLat, lng: pinLng, label: "Search center" }]
      : []),
    ...results.map((w) => ({ type: "well" as const, data: w })),
  ];

  const avgDist = results.length > 0
    ? results.reduce((s, w) => s + w.distance_miles, 0) / results.length
    : null;

  return (
    <div>
      <PageHeader title="Nearby Wells" description="Click the map or enter coordinates to find wells within a radius" />

      <div className="flex gap-4">
        <div className="w-56 shrink-0 space-y-4">
          <FilterPanel>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-500">Latitude</label>
              <input type="number" value={lat} onChange={(e) => setLat(e.target.value)}
                placeholder="e.g. 53.5"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-500">Longitude</label>
              <input type="number" value={lng} onChange={(e) => setLng(e.target.value)}
                placeholder="e.g. -115.0"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-slate-500">Radius (miles)</label>
              <input type="number" value={radius} onChange={(e) => setRadius(e.target.value)}
                min="1" max="500"
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
            </div>
            <SelectFilter label="Status Group" value={statusGroup} onChange={setStatusGroup} options={STATUS_OPTIONS} />
            <button onClick={handleSearch} disabled={!lat || !lng || loading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              <Search size={15} />
              {loading ? "Searching..." : "Search"}
            </button>
          </FilterPanel>

          {searched && (
            <div className="space-y-3">
              <StatCard label="Wells Found" value={results.length} icon={MapPin} />
              {avgDist != null && (
                <StatCard label="Avg Distance" value={`${avgDist.toFixed(1)} mi`} />
              )}
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0 space-y-4">
          <WellMap
            markers={markers}
            center={pinLat != null && pinLng != null ? [pinLat, pinLng] : [53.5, -115.0]}
            zoom={pinLat != null ? 8 : 5}
            height="420px"
            onMapClick={handleMapClick}
            radiusCircle={pinLat != null && pinLng != null
              ? { lat: pinLat, lng: pinLng, radiusMiles: parseFloat(radius) || 50 }
              : undefined}
          />
          {searched && (
            <DataTable
              columns={COLUMNS}
              data={results}
              keyField="id"
              loading={loading}
              emptyMessage="No wells found within the specified radius."
            />
          )}
        </div>
      </div>
    </div>
  );
}
