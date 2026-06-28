"use client";

import dynamic from "next/dynamic";
import { ArrowLeft } from "lucide-react";
import FilterPanel, { RadioFilter, CheckboxFilter, MultiSelectFilter } from "@/components/ui/FilterPanel";
import { formatNumber } from "@/lib/utils";
import { useWells } from "./useWells";
import {
  MAP_STYLE_OPTIONS,
  FORMAT_OPTIONS,
  STATUS_OPTIONS,
  HOLE_OPTIONS,
} from "./constants";

const WellMap = dynamic(() => import("@/components/maps/WellMap"), { ssr: false });

export default function WellsPage() {
  const {
    loading, sectionsLoading, tileStyle, format, statusGroup, holeType,
    orphanOnly, showSubs, selTownships, selRanges, selMeridians, selectedStrm,
    setTileStyle, setFormat, setStatusGroup, setHoleType,
    setOrphanOnly, setShowSubs, setSelTownships, setSelRanges, setSelMeridians,
    setSelectedStrm,
    filteredWells, sections, topSection,
    townshipOptions, rangeOptions, meridianOptions,
    markers, mapCenter, mapZoom,
    idleCount, horizCount,
    reset,
  } = useWells();

  return (
    <div className="flex gap-4">

      {/* Filter sidebar — scrollable */}
      <div className="w-56 shrink-0">
        <FilterPanel onReset={reset} className="overflow-y-auto max-h-[calc(100vh-6rem)]">
          <RadioFilter label="Map Style"   value={tileStyle}   onChange={setTileStyle}   options={MAP_STYLE_OPTIONS} />
          <RadioFilter label="Format"      value={format}      onChange={setFormat}       options={FORMAT_OPTIONS}    />
          <RadioFilter label="Well Status" value={statusGroup} onChange={setStatusGroup}  options={STATUS_OPTIONS}    />
          <CheckboxFilter label="Orphan wells only" checked={orphanOnly} onChange={setOrphanOnly} />
          <RadioFilter label="Hole Type"   value={holeType}    onChange={setHoleType}     options={HOLE_OPTIONS}      />
          <CheckboxFilter label="Show Substations"  checked={showSubs}   onChange={setShowSubs}   />
          {format === "ATS" && (
            <>
              <MultiSelectFilter label="Township" values={selTownships} onChange={setSelTownships} options={townshipOptions} />
              <MultiSelectFilter label="Range"    values={selRanges}    onChange={setSelRanges}    options={rangeOptions}    />
              <MultiSelectFilter label="Meridian" values={selMeridians} onChange={setSelMeridians} options={meridianOptions} />
            </>
          )}
        </FilterPanel>
      </div>

      {/* Right column: KPIs + banner + map */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">

        {/* KPI cards */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Total Wells</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(filteredWells.length)}
            </p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">IDLE</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading ? "…" : formatNumber(idleCount)}
            </p>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">
              {format === "ATS" ? "Sections" : "Horizontal"}
            </p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {loading || sectionsLoading
                ? "…"
                : format === "ATS"
                  ? formatNumber(sections.length)
                  : formatNumber(horizCount)}
            </p>
          </div>
        </div>

        {/* Top-volume section banner — ATS only */}
        {format === "ATS" && topSection && !loading && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-3 flex items-center gap-6">
            <div>
              <p className="text-xs font-medium text-emerald-700">Top Volume Section</p>
              <p className="text-lg font-bold text-emerald-900">{topSection.strm}</p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Volume</p>
              <p className="text-sm font-semibold text-emerald-800">
                {topSection.totalVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })} m³
              </p>
            </div>
            <div>
              <p className="text-xs text-emerald-600">Wells</p>
              <p className="text-sm font-semibold text-emerald-800">{topSection.wellCount}</p>
            </div>
            <button
              onClick={() => setSelectedStrm(topSection.strm)}
              className="ml-auto text-xs font-medium text-emerald-700 underline hover:text-emerald-900 transition-colors"
            >
              View on map →
            </button>
          </div>
        )}

        {/* Back button + map */}
        {selectedStrm && (
          <button
            onClick={() => setSelectedStrm(null)}
            className="flex items-center gap-1.5 self-start text-sm text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft size={15} />
            Back to sections
          </button>
        )}

        <WellMap
          markers={markers}
          center={mapCenter}
          zoom={mapZoom}
          height="calc(100vh - 18rem)"
          tileStyle={tileStyle}
          onSectionClick={setSelectedStrm}
          wellColorMode={format === "NTS" ? "volume" : "status"}
        />

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-slate-500 px-1">
          {format === "ATS" && !selectedStrm ? (
            <>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-full bg-emerald-200 border border-emerald-700" />
                Low volume
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-full bg-emerald-800 border border-emerald-900" />
                High volume
              </span>
              <span className="ml-auto italic opacity-75">Click a section to drill down</span>
            </>
          ) : (
            <>
              <span className="flex items-center gap-1.5"><span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500" />IDLE</span>
              <span className="flex items-center gap-1.5"><span className="inline-block w-2.5 h-2.5 rounded-full bg-amber-400"  />SUSP</span>
              <span className="flex items-center gap-1.5"><span className="inline-block w-2.5 h-2.5 rounded-full bg-red-500"    />ABD</span>
              {showSubs && <span className="flex items-center gap-1.5"><span className="inline-block w-2.5 h-2.5 rounded bg-violet-500" />Substation</span>}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
