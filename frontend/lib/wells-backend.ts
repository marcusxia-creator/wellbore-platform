/**
 * Wells data layer — talks directly to the Django backend.
 *
 * Unlike `lib/api.ts` (which switches between mock and real via
 * NEXT_PUBLIC_USE_MOCK), this module always hits the real API. The wells page
 * uses it so it renders live backend data regardless of the global mock flag,
 * while the other, not-yet-wired pages keep working against the mock layer.
 *
 * Endpoints (from the backend `apps/wells/urls.py`):
 *   GET /wells/                          paginated wells (100 / page)
 *   GET /well-statuses/                  status categories        [{value,label}]
 *   GET /well-types/                     well types               [{value,label}]
 *   GET /production-injection-formations/ formations              [{value,label}]
 */
import axios from "axios";
import type { ApiWell, FilterOption, PaginatedResponse } from "./types";
import { getAccessToken } from "./auth";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
  // Repeat array params without brackets (prod_inject_frmtn=a&prod_inject_frmtn=b)
  // so Django's request.query_params.getlist() picks them all up.
  paramsSerializer: { indexes: null },
});

// The wells endpoints are public, but attach a JWT when we have one so this
// keeps working if the backend later requires auth.
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─── Query params supported by GET /wells/ ───────────────────────────────────

export interface WellQuery {
  search?: string;
  status?: string;              // status category: Active | Inactive | Suspended | ABD
  actual_status?: string;
  well_type?: string;
  prod_inject_frmtn?: string[]; // one or more formations
}

function toParams(q: WellQuery, page: number): Record<string, unknown> {
  const params: Record<string, unknown> = { page };
  if (q.search) params.search = q.search;
  if (q.status) params.status = q.status;
  if (q.actual_status) params.actual_status = q.actual_status;
  if (q.well_type) params.well_type = q.well_type;
  if (q.prod_inject_frmtn?.length) params.prod_inject_frmtn = q.prod_inject_frmtn;
  return params;
}

// ─── Wells ───────────────────────────────────────────────────────────────────

export async function fetchApiWells(
  q: WellQuery = {},
  page = 1
): Promise<PaginatedResponse<ApiWell>> {
  const { data } = await api.get<PaginatedResponse<ApiWell>>("/wells/", {
    params: toParams(q, page),
  });
  return data;
}

/** Upper bound on how many wells we pull for the map at once. */
export const MAP_WELL_LIMIT = 1000;

/** How many page requests to have in flight at once. Kept low so a filtered
 *  scan (each page runs a DISTINCT-ON sort server-side) doesn't overwhelm the
 *  database with concurrent heavy queries. */
const PAGE_CONCURRENCY = 4;

/**
 * Load a bounded sample of wells matching the filters for map display, along
 * with the true total match count. The backend paginates at 100/page, so this
 * pulls the first few pages in small concurrent batches up to `limit`.
 */
export async function fetchWellsForMap(
  q: WellQuery = {},
  limit = MAP_WELL_LIMIT
): Promise<{ wells: ApiWell[]; total: number }> {
  const first = await fetchApiWells(q, 1);
  const total = first.count;
  const pageSize = first.results.length || 100;

  const pagesNeeded = Math.min(
    Math.ceil(limit / pageSize),
    Math.ceil(total / pageSize) || 1
  );

  // Remaining page numbers (2..pagesNeeded), fetched in bounded-concurrency batches.
  const pages = Array.from({ length: Math.max(0, pagesNeeded - 1) }, (_, i) => i + 2);
  const rest: ApiWell[] = [];
  for (let i = 0; i < pages.length; i += PAGE_CONCURRENCY) {
    const batch = pages.slice(i, i + PAGE_CONCURRENCY);
    const results = await Promise.all(
      batch.map((page) =>
        fetchApiWells(q, page)
          .then((r) => r.results)
          .catch(() => [] as ApiWell[])
      )
    );
    rest.push(...results.flat());
  }

  const wells = [...first.results, ...rest].slice(0, limit);
  return { wells, total };
}

// ─── Filter options (metadata) ───────────────────────────────────────────────

export async function fetchWellStatuses(): Promise<FilterOption[]> {
  const { data } = await api.get<FilterOption[]>("/well-statuses/");
  return data;
}

export async function fetchWellTypes(): Promise<FilterOption[]> {
  const { data } = await api.get<FilterOption[]>("/well-types/");
  return data;
}

export async function fetchProductionInjectionFormations(): Promise<FilterOption[]> {
  const { data } = await api.get<FilterOption[]>("/production-injection-formations/");
  return data;
}

export default api;
