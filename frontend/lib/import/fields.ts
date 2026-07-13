/**
 * Well field definitions for raw data import: header auto-mapping,
 * type coercion, and row validation.
 */
import type { Well } from "@/lib/types";

export type FieldType = "string" | "number" | "boolean";

export interface FieldDef {
  key: keyof Omit<Well, "id">;
  label: string;
  type: FieldType;
  required?: boolean;
  /** Normalized header aliases that auto-map to this field. */
  aliases: string[];
}

/** Lowercase and strip everything except letters and digits. */
export function normalizeHeader(h: string): string {
  return h.toLowerCase().replace(/[^a-z0-9]/g, "");
}

export const WELL_FIELDS: FieldDef[] = [
  { key: "well_id",             label: "Well ID",             type: "string",  aliases: ["wellid"] },
  { key: "uwi",                 label: "UWI",                 type: "string",  required: true, aliases: ["uwi", "uniquewellidentifier"] },
  { key: "area",                label: "Area",                type: "string",  aliases: ["area", "province"] },
  { key: "surf_latitude",       label: "Surface Latitude",    type: "number",  required: true, aliases: ["surflatitude", "latitude", "lat", "surfacelatitude"] },
  { key: "surf_longitude",      label: "Surface Longitude",   type: "number",  required: true, aliases: ["surflongitude", "longitude", "long", "lon", "lng", "surfacelongitude"] },
  { key: "well_status_text",    label: "Status Text",         type: "string",  aliases: ["wellstatustext", "statustext", "status"] },
  { key: "well_status_group",   label: "Status Group",        type: "string",  aliases: ["wellstatusgroup", "statusgroup"] },
  { key: "available_volume_m3", label: "Available Volume m³", type: "number",  aliases: ["availablevolumem3", "volume", "volumem3", "availablevolume"] },
  { key: "legal_subdivisions",  label: "Legal Subdivisions",  type: "number",  aliases: ["legalsubdivisions", "lsd"] },
  { key: "section",             label: "Section",             type: "number",  aliases: ["section", "sec"] },
  { key: "township",            label: "Township",            type: "number",  aliases: ["township", "twp"] },
  { key: "range",               label: "Range",               type: "number",  aliases: ["range", "rge"] },
  { key: "meridian",            label: "Meridian",            type: "number",  aliases: ["meridian", "mer"] },
  { key: "crooked_hole",        label: "Crooked Hole",        type: "boolean", aliases: ["crookedholetf", "crookedhole", "crooked"] },
  { key: "deviated_hole",       label: "Deviated Hole",       type: "boolean", aliases: ["deviatedholetf", "deviatedhole", "deviated"] },
  { key: "horizontal_hole",     label: "Horizontal Hole",     type: "boolean", aliases: ["horizontalholetf", "horizontalhole", "horizontal"] },
  { key: "burst_pressure_psi",  label: "Burst Pressure psi",  type: "number",  aliases: ["burstpressurepsi", "burstpressure"] },
  { key: "format",              label: "Format",              type: "string",  aliases: ["format"] },
  { key: "strm",                label: "STRM",                type: "string",  aliases: ["strm"] },
  { key: "orphan",              label: "Orphan",              type: "boolean", aliases: ["orphan", "orphantf", "orphanwell"] },
];

/** header text → field key (or "" for ignore) */
export type ColumnMapping = Record<string, string>;

/** Auto-map spreadsheet headers to well fields by normalized alias. */
export function autoMapColumns(headers: string[]): ColumnMapping {
  const mapping: ColumnMapping = {};
  const taken = new Set<string>();
  for (const header of headers) {
    const norm = normalizeHeader(header);
    const field = WELL_FIELDS.find(
      (f) => !taken.has(f.key) && (f.key.replace(/_/g, "") === norm || f.aliases.includes(norm))
    );
    mapping[header] = field ? field.key : "";
    if (field) taken.add(field.key);
  }
  return mapping;
}

// ─── Coercion ────────────────────────────────────────────────────────────────

function toNumber(v: unknown): number | null {
  if (v == null || v === "") return null;
  const n = typeof v === "number" ? v : parseFloat(String(v).replace(/,/g, ""));
  return Number.isFinite(n) ? n : null;
}

function toBoolean(v: unknown): boolean {
  if (typeof v === "boolean") return v;
  if (typeof v === "number") return v !== 0;
  const s = String(v ?? "").trim().toUpperCase();
  return s === "T" || s === "TRUE" || s === "Y" || s === "YES" || s === "1";
}

export interface RowIssue {
  rowNumber: number; // 1-based spreadsheet data row
  reason: string;
}

export interface BuildResult {
  wells: Well[];
  skipped: RowIssue[];
}

/**
 * Convert raw parsed rows into Well objects using the given column mapping.
 * Rows missing required fields are skipped and reported.
 */
export function buildWells(
  rows: Record<string, unknown>[],
  mapping: ColumnMapping,
  startId = 1
): BuildResult {
  // Invert: field key → header
  const headerFor: Partial<Record<string, string>> = {};
  for (const [header, key] of Object.entries(mapping)) {
    if (key) headerFor[key] = header;
  }

  const wells: Well[] = [];
  const skipped: RowIssue[] = [];

  rows.forEach((row, i) => {
    const rowNumber = i + 1;
    const get = (key: string) => {
      const h = headerFor[key];
      return h != null ? row[h] : null;
    };

    const uwi = String(get("uwi") ?? "").trim();
    const lat = toNumber(get("surf_latitude"));
    const lon = toNumber(get("surf_longitude"));

    if (!uwi) { skipped.push({ rowNumber, reason: "Missing UWI" }); return; }
    if (lat == null || lon == null) {
      skipped.push({ rowNumber, reason: "Missing or invalid coordinates" });
      return;
    }
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      skipped.push({ rowNumber, reason: "Coordinates out of range" });
      return;
    }

    wells.push({
      id: startId + wells.length,
      well_id:             String(get("well_id") ?? uwi).trim() || uwi,
      uwi,
      area:                String(get("area") ?? "").trim(),
      surf_latitude:       lat,
      surf_longitude:      lon,
      well_status_text:    String(get("well_status_text") ?? "").trim(),
      well_status_group:   String(get("well_status_group") ?? "").trim().toUpperCase(),
      available_volume_m3: toNumber(get("available_volume_m3")) ?? 0,
      legal_subdivisions:  toNumber(get("legal_subdivisions")) ?? 0,
      section:             toNumber(get("section")) ?? 0,
      township:            toNumber(get("township")) ?? 0,
      range:               toNumber(get("range")) ?? 0,
      meridian:            toNumber(get("meridian")) ?? 0,
      crooked_hole:        toBoolean(get("crooked_hole")),
      deviated_hole:       toBoolean(get("deviated_hole")),
      horizontal_hole:     toBoolean(get("horizontal_hole")),
      burst_pressure_psi:  toNumber(get("burst_pressure_psi")) ?? 0,
      format:              String(get("format") ?? "").trim().toUpperCase(),
      strm:                String(get("strm") ?? "").trim(),
      orphan:              toBoolean(get("orphan")),
    });
  });

  return { wells, skipped };
}
