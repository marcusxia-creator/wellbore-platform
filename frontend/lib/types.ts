// ─── Well (flat shape used by the client-side import + map markers) ──────────

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

// ─── Backend (Django) Well ───────────────────────────────────────────────────
// Shape returned by GET /api/wells/ (see backend apps/wells/serializers.py).

export interface ApiWell {
  id: string;                 // base_uwi
  uwi: string;
  name: string | null;
  operator: string | null;
  field_name: string | null;
  status: string;             // "Active" | "Inactive" | "Suspended" | "ABD"
  actual_status_text: string;
  well_type: string | null;
  latitude: number | null;
  longitude: number | null;
  province_state: string;
  country: string;
  spud_date: string | null;
  rig_release_date: string | null;
  true_vertical_depth_m: number | null;
  measured_depth_m: number | null;
  created_at: string | null;
  updated_at: string | null;
}

// ─── Map ───────────────────────────────────────────────────────────────────

export type MapMarker = { type: "well"; data: Well };

// ─── Shared ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next: number | null;
  previous: number | null;
  results: T[];
}

export interface FilterOption {
  value: string;
  label: string;
}
