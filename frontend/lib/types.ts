// ─── Well ──────────────────────────────────────────────────────────────────

export interface Well {
  id: number;
  well_id: string;
  uwi: string;
  area: string;
  surf_latitude: number;
  surf_longitude: number;
  well_status_text: string;
  well_status_group: string;   // "IDLE" | "SUSP" | "ABD"
  available_volume_m3: number;
  legal_subdivisions: number;
  section: number;
  township: number;
  range: number;
  meridian: number;
  crooked_hole: boolean;
  deviated_hole: boolean;
  horizontal_hole: boolean;
  burst_pressure_psi: number;
  format: string;              // "ATS" | "NTS"
  strm: string;
  orphan: boolean;
}

export interface WellFilters {
  search?: string;
  well_status_group?: string;
  format?: string;
  area?: string;
  horizontal_hole?: boolean;
  deviated_hole?: boolean;
  orphan?: boolean;
}

export interface SectionFilters {
  well_status_group?: string;  // omit or "ALL" = no filter
  horizontal_hole?: boolean;
  deviated_hole?: boolean;
  orphan?: boolean;
  township?: number[];
  range?: number[];
  meridian?: number[];
  area?: string;
}

// ─── Substation ────────────────────────────────────────────────────────────

export interface Substation {
  id: number;
  facility_code: string;       // e.g. "2S"
  name: string;                // Facility Name
  land_location: string;       // e.g. "25-8-W 5"
  township: number;
  range: number;
  meridian: number;
  latitude: number;
  longitude: number;
  capacity_mw: number | null;  // CAPACITY (MW)
  address: string;
  area: string;                // AB | SK | BC
  nearby_well_count: number;   // computed
}

export interface SubstationFilters {
  search?: string;
  area?: string;
}

// ─── Nearby Wells ──────────────────────────────────────────────────────────

export interface NearbyWellsParams {
  latitude: number;
  longitude: number;
  radius_miles: number;
  well_status_group?: string;
}

export interface NearbyWellResult extends Well {
  distance_miles: number;
}

// ─── Best Point ────────────────────────────────────────────────────────────

export interface BestPointParams {
  search_area: { north: number; south: number; east: number; west: number };
  radius_miles: number;
  min_wells: number;
  well_status_group?: string;
}

export interface BestPoint {
  latitude: number;
  longitude: number;
  well_count: number;
  avg_volume_m3: number | null;
  score: number;
  nearby_wells: NearbyWellResult[];
}

// ─── Rankings ──────────────────────────────────────────────────────────────

export interface WellRanking {
  rank: number;
  well: Well;
  score: number;
  volume_rank: number;
  pressure_rank: number;
}

export interface SubstationRanking {
  rank: number;
  substation: Substation;
  score: number;
  well_density: number;
  capacity_utilization: number | null;
}

export interface SubstationCandidate {
  id: number;
  latitude: number;
  longitude: number;
  score: number;
  nearby_well_count: number;
  avg_well_depth_ft: number;
  county: string;
  state: string;
  estimated_load_mva: number;
}

// ─── Map ───────────────────────────────────────────────────────────────────

export interface WellSection {
  strm: string;
  lat: number;
  lng: number;
  wellCount: number;
  totalVolume: number;
}

export type MapMarker =
  | { type: "well"; data: Well | NearbyWellResult }
  | { type: "substation"; data: Substation }
  | { type: "bestPoint"; data: BestPoint }
  | { type: "pin"; lat: number; lng: number; label?: string }
  | { type: "section"; data: WellSection };

// ─── Shared ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FilterOption {
  value: string;
  label: string;
}
