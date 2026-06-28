import { useState, useEffect, useMemo } from "react";
import type { Well, Substation, MapMarker, WellSection } from "@/lib/types";
import { fetchSubstations } from "@/lib/api";
import { useWellsStore } from "@/lib/wells-store";

// ── STRM key — used only for drill-down well matching ────────────────────────

export function wellStrm(w: Well): string {
  return w.strm || `${w.section}-${w.township}-${w.range}-${w.meridian}`;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useWells() {
  const { allWells, wellsLoading: loading } = useWellsStore();

  const [allSubstations, setAllSubstations]       = useState<Substation[]>([]);
  const [substationsLoaded, setSubstationsLoaded] = useState(false);

  // Filters
  const [tileStyle,    setTileStyle]    = useState("basic");
  const [format,       setFormat]       = useState("ATS");
  const [statusGroup,  setStatusGroup]  = useState("ALL");
  const [holeType,     setHoleType]     = useState("ALL");
  const [orphanOnly,   setOrphanOnly]   = useState(false);
  const [showSubs,     setShowSubs]     = useState(false);

  // ATS location filters
  const [selTownships, setSelTownships] = useState<(string | number)[]>([]);
  const [selRanges,    setSelRanges]    = useState<(string | number)[]>([]);
  const [selMeridians, setSelMeridians] = useState<(string | number)[]>([]);

  // Drill-down
  const [selectedStrm, setSelectedStrm] = useState<string | null>(null);

  useEffect(() => {
    if (showSubs && !substationsLoaded) {
      fetchSubstations({}, 1, 10000)
        .then((res) => { setAllSubstations(res.results); setSubstationsLoaded(true); })
        .catch(() => {});
    }
  }, [showSubs, substationsLoaded]);

  // Reset drill-down when format changes
  useEffect(() => { setSelectedStrm(null); }, [format]);

  // ── Derived data ──────────────────────────────────────────────────────────────

  const filteredWells = useMemo(() => {
    let out = allWells.filter((w) => w.format === format);
    if (statusGroup !== "ALL")     out = out.filter((w) => w.well_status_group === statusGroup);
    if (orphanOnly)                out = out.filter((w) => w.orphan);
    if (holeType === "Horizontal") out = out.filter((w) => w.horizontal_hole);
    if (holeType === "Deviated")   out = out.filter((w) => w.deviated_hole);
    if (format === "ATS") {
      if (selTownships.length > 0) out = out.filter((w) => selTownships.includes(w.township));
      if (selRanges.length    > 0) out = out.filter((w) => selRanges.includes(w.range));
      if (selMeridians.length > 0) out = out.filter((w) => selMeridians.includes(w.meridian));
    }
    return out;
  }, [allWells, format, statusGroup, orphanOnly, holeType, selTownships, selRanges, selMeridians]);

  // sections: derived synchronously from filteredWells — keeps map and cards in sync
  const sections = useMemo<WellSection[]>(() => {
    if (format !== "ATS") return [];
    const map = new Map<string, { ws: Well[]; vol: number }>();
    for (const w of filteredWells) {
      if (!w.surf_latitude || !w.surf_longitude) continue;
      if (!w.section || !w.township || !w.range || !w.meridian) continue;
      const key = wellStrm(w);
      if (!map.has(key)) map.set(key, { ws: [], vol: 0 });
      const entry = map.get(key)!;
      entry.ws.push(w);
      entry.vol += w.available_volume_m3 ?? 0;
    }
    return Array.from(map.entries()).map(([strm, { ws, vol }]) => ({
      strm,
      lat: ws.reduce((s, w) => s + w.surf_latitude,  0) / ws.length,
      lng: ws.reduce((s, w) => s + w.surf_longitude, 0) / ws.length,
      wellCount: ws.length,
      totalVolume: vol,
    }));
  }, [filteredWells, format]);

  const topSection = useMemo(() =>
    sections.length === 0 ? null
      : sections.reduce((a, b) => a.totalVolume > b.totalVolume ? a : b),
    [sections]
  );

  // ATS dropdown options derived from all ATS wells (not filtered)
  const atsWells = useMemo(() => allWells.filter((w) => w.format === "ATS"), [allWells]);
  const townshipOptions = useMemo(() =>
    [...new Set(atsWells.map((w) => w.township))].filter((t) => t > 0).sort((a, b) => a - b),
    [atsWells]);
  const rangeOptions = useMemo(() =>
    [...new Set(atsWells.map((w) => w.range))].filter((r) => r > 0).sort((a, b) => a - b),
    [atsWells]);
  const meridianOptions = useMemo(() =>
    [...new Set(atsWells.map((w) => w.meridian))].filter((m) => m > 0).sort((a, b) => a - b),
    [atsWells]);

  const subMarkers = useMemo<MapMarker[]>(() =>
    showSubs ? allSubstations.map((s) => ({ type: "substation" as const, data: s })) : [],
    [showSubs, allSubstations]);

  const markers = useMemo<MapMarker[]>(() => {
    if (format === "ATS" && !selectedStrm) {
      return [
        ...sections.map((s) => ({ type: "section" as const, data: s })),
        ...subMarkers,
      ];
    }
    const displayWells = selectedStrm
      ? filteredWells.filter((w) => wellStrm(w) === selectedStrm)
      : filteredWells;
    return [
      ...displayWells.map((w) => ({ type: "well" as const, data: w })),
      ...subMarkers,
    ];
  }, [format, selectedStrm, sections, filteredWells, subMarkers]);

  const { mapCenter, mapZoom } = useMemo<{ mapCenter: [number, number]; mapZoom: number }>(() => {
    if (selectedStrm) {
      const sec = sections.find((s) => s.strm === selectedStrm);
      if (sec) return { mapCenter: [sec.lat, sec.lng], mapZoom: 11 };
    }
    return { mapCenter: [53.5, -115.0], mapZoom: 6 };
  }, [selectedStrm, sections]);

  const idleCount  = useMemo(() => filteredWells.filter((w) => w.well_status_group === "IDLE").length, [filteredWells]);
  const horizCount = useMemo(() => filteredWells.filter((w) => w.horizontal_hole).length, [filteredWells]);

  const reset = () => {
    setStatusGroup("ALL"); setHoleType("ALL"); setOrphanOnly(false);
    setShowSubs(false); setSelTownships([]); setSelRanges([]); setSelMeridians([]);
    setSelectedStrm(null);
  };

  return {
    // state
    loading, tileStyle, format, statusGroup, holeType,
    orphanOnly, showSubs, selTownships, selRanges, selMeridians, selectedStrm,
    // setters
    setTileStyle, setFormat, setStatusGroup, setHoleType,
    setOrphanOnly, setShowSubs, setSelTownships, setSelRanges, setSelMeridians,
    setSelectedStrm,
    // derived
    filteredWells, sections, topSection,
    townshipOptions, rangeOptions, meridianOptions,
    markers, mapCenter, mapZoom,
    idleCount, horizCount,
    // actions
    reset,
  };
}
