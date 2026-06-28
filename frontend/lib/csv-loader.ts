/**
 * Singleton CSV loader — fetches and parses the two data files once,
 * then caches the results in memory for the rest of the session.
 *
 * Files must be at:
 *   /public/data/AB_SK_BC_dash.csv
 *   /public/data/Substations_AB_SK_BC.csv
 */
import Papa from "papaparse";
import type { Well, Substation } from "./types";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function parseBool(v: string): boolean {
  return v?.trim().toUpperCase() === "T";
}

function parseNum(v: string, fallback = 0): number {
  const n = parseFloat(v);
  return isNaN(n) ? fallback : n;
}

function parseCSV<T>(url: string): Promise<T[]> {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      skipEmptyLines: true,
      // Strip UTF-8 BOM if present
      beforeFirstChunk: (chunk: string) => chunk.replace(/^﻿/, ""),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      complete: (results: any) => resolve(results.data as T[]),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      error: (err: any) => reject(err),
    });
  });
}

// ─── Wells ───────────────────────────────────────────────────────────────────

type RawWell = Record<string, string>;

function transformWell(raw: RawWell, id: number): Well {
  return {
    id,
    well_id:              raw["Well_ID"]             ?? "",
    uwi:                  raw["UWI"]                 ?? "",
    area:                 raw["Area"]                ?? "",
    surf_latitude:        parseNum(raw["Surf_Latitude"]),
    surf_longitude:       parseNum(raw["Surf_Longitude"]),
    well_status_text:     raw["Well_Status_Text"]    ?? "",
    well_status_group:    raw["Well_Status_Group"]   ?? "",
    available_volume_m3:  parseNum(raw["Available_Volume_m3"]),
    legal_subdivisions:   parseNum(raw["Legal Subdivisions"]),
    section:              parseNum(raw["Section"]),
    township:             parseNum(raw["Township"]),
    range:                parseNum(raw["Range"]),
    meridian:             parseNum(raw["Meridian"]),
    crooked_hole:         parseBool(raw["Crooked_Hole_TF"]),
    deviated_hole:        parseBool(raw["Deviated_Hole_TF"]),
    horizontal_hole:      parseBool(raw["Horizontal_Hole_TF"]),
    burst_pressure_psi:   parseNum(raw["Burst_Pressure_psi"]),
    format:               raw["Format"]              ?? "",
    strm:                 raw["STRM"]                ?? "",
    orphan:               raw["orphan"] === "1",
  };
}

let _wellsPromise: Promise<Well[]> | null = null;

export function loadWells(): Promise<Well[]> {
  if (!_wellsPromise) {
    _wellsPromise = parseCSV<RawWell>("/data/AB_SK_BC_dash.csv").then((rows) =>
      rows
        .filter((r) => r["Surf_Latitude"] && r["Surf_Longitude"])
        .map((r, i) => transformWell(r, i + 1))
    );
  }
  return _wellsPromise;
}

// ─── Substations ─────────────────────────────────────────────────────────────

type RawSubstation = Record<string, string>;

function transformSubstation(raw: RawSubstation, id: number): Substation {
  const capRaw = raw["CAPACITY (MW)"];
  const cap = capRaw && capRaw.trim() !== "" ? parseNum(capRaw) : null;
  return {
    id,
    facility_code: raw["Facility Code"] ?? "",
    name:          raw["Facility Name"] ?? "",
    land_location: raw["Land Location"] ?? "",
    township:      parseNum(raw["Township"]),
    range:         parseNum(raw["Range"]),
    meridian:      parseNum(raw["Meridian"]),
    latitude:      parseNum(raw["Latitude"]),
    longitude:     parseNum(raw["Longitude"]),
    capacity_mw:   cap,
    address:       raw["ADDRESS"]       ?? "",
    area:          raw["Area"]          ?? "",
    nearby_well_count: 0, // computed on demand
  };
}

let _substationsPromise: Promise<Substation[]> | null = null;

export function loadSubstations(): Promise<Substation[]> {
  if (!_substationsPromise) {
    _substationsPromise = parseCSV<RawSubstation>("/data/Substations_AB_SK_BC.csv").then(
      (rows) =>
        rows
          .filter((r) => r["Latitude"] && r["Longitude"])
          .map((r, i) => transformSubstation(r, i + 1))
    );
  }
  return _substationsPromise;
}
