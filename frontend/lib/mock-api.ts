import type {
  WellFilters, SectionFilters, SubstationFilters,
  NearbyWellsParams, BestPointParams,
  PaginatedResponse, Well, WellSection, Substation,
  NearbyWellResult, BestPoint,
  WellRanking, SubstationRanking, SubstationCandidate,
} from "./types";
import { loadWells, loadSubstations } from "./csv-loader";

// ─── Wells ───────────────────────────────────────────────────────────────────

export async function fetchWells(
  filters: WellFilters = {}, page = 1, pageSize = 1000
): Promise<PaginatedResponse<Well>> {
  let results = await loadWells();

  if (filters.search) {
    const q = filters.search.toLowerCase();
    results = results.filter(
      (w) => w.uwi.toLowerCase().includes(q) || w.strm.toLowerCase().includes(q)
    );
  }
  if (filters.well_status_group) results = results.filter((w) => w.well_status_group === filters.well_status_group);
  if (filters.format)            results = results.filter((w) => w.format === filters.format);
  if (filters.area)              results = results.filter((w) => w.area === filters.area);
  if (filters.horizontal_hole != null) results = results.filter((w) => w.horizontal_hole === filters.horizontal_hole);
  if (filters.deviated_hole != null)   results = results.filter((w) => w.deviated_hole === filters.deviated_hole);
  if (filters.orphan != null)          results = results.filter((w) => w.orphan === filters.orphan);

  const count = results.length;
  const start = (page - 1) * pageSize;
  return { count, next: null, previous: null, results: results.slice(start, start + pageSize) };
}

export async function fetchWell(id: number): Promise<Well> {
  const wells = await loadWells();
  const w = wells.find((x) => x.id === id);
  if (!w) throw new Error(`Well ${id} not found`);
  return w;
}

export async function fetchWellFilterOptions() {
  const wells = await loadWells();
  const areas = [...new Set(wells.map((w) => w.area).filter(Boolean))].sort();
  return {
    statuses: [
      { value: "IDLE", label: "IDLE (Active)" },
      { value: "SUSP", label: "SUSP (Suspended)" },
      { value: "ABD",  label: "ABD (Abandoned)" },
    ],
    formats: [
      { value: "ATS", label: "ATS" },
      { value: "NTS", label: "NTS" },
    ],
    areas: areas.map((v) => ({ value: v, label: v })),
  };
}

// ─── Sections ────────────────────────────────────────────────────────────────

function wellStrm(w: Well): string {
  return w.strm || `${w.section}-${w.township}-${w.range}-${w.meridian}`;
}

export async function fetchSections(filters: SectionFilters = {}): Promise<WellSection[]> {
  let wells = await loadWells();

  // Sections only exist for ATS format
  wells = wells.filter((w) => w.format === "ATS");

  if (filters.well_status_group) wells = wells.filter((w) => w.well_status_group === filters.well_status_group);
  if (filters.orphan != null)    wells = wells.filter((w) => w.orphan === filters.orphan);
  if (filters.horizontal_hole)   wells = wells.filter((w) => w.horizontal_hole);
  if (filters.deviated_hole)     wells = wells.filter((w) => w.deviated_hole);
  if (filters.area)              wells = wells.filter((w) => w.area === filters.area);
  if (filters.township?.length)  wells = wells.filter((w) => filters.township!.includes(w.township));
  if (filters.range?.length)     wells = wells.filter((w) => filters.range!.includes(w.range));
  if (filters.meridian?.length)  wells = wells.filter((w) => filters.meridian!.includes(w.meridian));

  const map = new Map<string, { wells: Well[]; totalVolume: number }>();
  for (const w of wells) {
    if (!w.surf_latitude || !w.surf_longitude) continue;
    if (!w.section || !w.township || !w.range || !w.meridian) continue;
    const key = wellStrm(w);
    if (!map.has(key)) map.set(key, { wells: [], totalVolume: 0 });
    const s = map.get(key)!;
    s.wells.push(w);
    s.totalVolume += w.available_volume_m3 ?? 0;
  }

  return Array.from(map.entries()).map(([strm, { wells: ws, totalVolume }]) => ({
    strm,
    lat: ws.reduce((sum, w) => sum + w.surf_latitude, 0) / ws.length,
    lng: ws.reduce((sum, w) => sum + w.surf_longitude, 0) / ws.length,
    wellCount: ws.length,
    totalVolume,
  }));
}

// ─── Substations ─────────────────────────────────────────────────────────────

export async function fetchSubstations(
  filters: SubstationFilters = {}, page = 1, pageSize = 1000
): Promise<PaginatedResponse<Substation>> {
  let results = await loadSubstations();

  if (filters.search) {
    const q = filters.search.toLowerCase();
    results = results.filter(
      (s) => s.name.toLowerCase().includes(q) || s.facility_code.toLowerCase().includes(q)
    );
  }
  if (filters.area) results = results.filter((s) => s.area === filters.area);

  const count = results.length;
  const start = (page - 1) * pageSize;
  return { count, next: null, previous: null, results: results.slice(start, start + pageSize) };
}

export async function fetchSubstation(id: number): Promise<Substation> {
  const subs = await loadSubstations();
  const s = subs.find((x) => x.id === id);
  if (!s) throw new Error(`Substation ${id} not found`);
  return s;
}

export async function fetchSubstationFilterOptions() {
  const subs = await loadSubstations();
  const areas = [...new Set(subs.map((s) => s.area).filter(Boolean))].sort();
  return {
    areas: areas.map((v) => ({ value: v, label: v })),
  };
}

// ─── Nearby Wells (with bounding-box pre-filter for performance) ──────────────

const R_EARTH = 3958.8;

function haversine(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R_EARTH * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export async function fetchNearbyWells(params: NearbyWellsParams): Promise<NearbyWellResult[]> {
  const wells = await loadWells();
  const { latitude, longitude, radius_miles } = params;

  // Bounding box pre-filter (fast)
  const latDelta = radius_miles / 69;
  const lngDelta = radius_miles / (Math.cos((latitude * Math.PI) / 180) * 69);
  const candidates = wells.filter(
    (w) =>
      w.surf_latitude  >= latitude  - latDelta &&
      w.surf_latitude  <= latitude  + latDelta &&
      w.surf_longitude >= longitude - lngDelta &&
      w.surf_longitude <= longitude + lngDelta
  );

  let results: NearbyWellResult[] = candidates
    .map((w) => ({ ...w, distance_miles: haversine(latitude, longitude, w.surf_latitude, w.surf_longitude) }))
    .filter((w) => w.distance_miles <= radius_miles);

  if (params.well_status_group) results = results.filter((w) => w.well_status_group === params.well_status_group);

  return results.sort((a, b) => a.distance_miles - b.distance_miles);
}

// ─── Best Point ───────────────────────────────────────────────────────────────

export async function fetchBestPoint(params: BestPointParams): Promise<BestPoint[]> {
  const wells = await loadWells();
  const { search_area, radius_miles, min_wells, well_status_group } = params;

  // Filter to search area
  let pool = wells.filter(
    (w) =>
      w.surf_latitude  >= search_area.south &&
      w.surf_latitude  <= search_area.north &&
      w.surf_longitude >= search_area.west  &&
      w.surf_longitude <= search_area.east
  );
  if (well_status_group) pool = pool.filter((w) => w.well_status_group === well_status_group);

  if (pool.length === 0) return [];

  // Sample candidate points from the pool itself and score each
  const stride = Math.max(1, Math.floor(pool.length / 50));
  const candidates: BestPoint[] = [];

  for (let i = 0; i < pool.length; i += stride) {
    const center = pool[i];
    const nearby = pool.filter(
      (w) => haversine(center.surf_latitude, center.surf_longitude, w.surf_latitude, w.surf_longitude) <= radius_miles
    );
    if (nearby.length < min_wells) continue;

    const volumes = nearby.map((w) => w.available_volume_m3).filter((v) => v > 0);
    const avg_volume_m3 = volumes.length > 0 ? volumes.reduce((a, b) => a + b, 0) / volumes.length : null;
    const maxNearby = Math.max(...pool.map((_, j) => {
      if (j % stride !== 0) return 0;
      return pool.filter((w) => haversine(pool[j].surf_latitude, pool[j].surf_longitude, w.surf_latitude, w.surf_longitude) <= radius_miles).length;
    }));
    const score = parseFloat(
      ((nearby.length / Math.max(maxNearby, 1)) * 0.7 + (avg_volume_m3 ? Math.min(avg_volume_m3 / 100, 1) * 0.3 : 0)).toFixed(4)
    );

    candidates.push({
      latitude: center.surf_latitude,
      longitude: center.surf_longitude,
      well_count: nearby.length,
      avg_volume_m3,
      score,
      nearby_wells: nearby.slice(0, 10).map((w) => ({
        ...w,
        distance_miles: haversine(center.surf_latitude, center.surf_longitude, w.surf_latitude, w.surf_longitude),
      })),
    });
  }

  return candidates.sort((a, b) => b.score - a.score).slice(0, 10);
}

// ─── Rankings ─────────────────────────────────────────────────────────────────

export async function fetchWellRankings(params?: { area?: string; limit?: number }): Promise<WellRanking[]> {
  const wells = await loadWells();
  let pool = wells.filter((w) => w.available_volume_m3 > 0);
  if (params?.area) pool = pool.filter((w) => w.area === params.area);

  pool.sort((a, b) => b.available_volume_m3 - a.available_volume_m3);
  const byPressure = [...pool].sort((a, b) => b.burst_pressure_psi - a.burst_pressure_psi);
  const pressureRankMap = new Map(byPressure.map((w, i) => [w.id, i + 1]));
  const topVol = pool[0]?.available_volume_m3 ?? 1;

  return pool.slice(0, params?.limit ?? 50).map((w, i) => ({
    rank: i + 1,
    well: w,
    score: parseFloat((w.available_volume_m3 / topVol).toFixed(4)),
    volume_rank: i + 1,
    pressure_rank: pressureRankMap.get(w.id) ?? 0,
  }));
}

export async function fetchSubstationRankings(params?: { area?: string; limit?: number }): Promise<SubstationRanking[]> {
  const [subs, wells] = await Promise.all([loadSubstations(), loadWells()]);
  let pool = [...subs];
  if (params?.area) pool = pool.filter((s) => s.area === params.area);

  // Compute well density (wells within ~20 miles)
  const scored = pool.map((s) => {
    const nearby = wells.filter(
      (w) => haversine(s.latitude, s.longitude, w.surf_latitude, w.surf_longitude) <= 20
    ).length;
    return { ...s, nearby_well_count: nearby };
  });

  scored.sort((a, b) => b.nearby_well_count - a.nearby_well_count);
  const topCount = scored[0]?.nearby_well_count ?? 1;

  return scored.slice(0, params?.limit ?? 50).map((s, i) => ({
    rank: i + 1,
    substation: s,
    score: parseFloat((s.nearby_well_count / Math.max(topCount, 1)).toFixed(4)),
    well_density: parseFloat((s.nearby_well_count / 100).toFixed(3)),
    capacity_utilization: s.capacity_mw != null ? Math.min(0.95, 0.4 + i * 0.01) : null,
  }));
}

export async function fetchSubstationCandidates(_params?: {
  county?: string;
  min_wells?: number;
  limit?: number;
}): Promise<SubstationCandidate[]> {
  // Candidate scoring is an algorithmic output — use the real API for this.
  return [];
}
