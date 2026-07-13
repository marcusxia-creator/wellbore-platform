import axios from "axios";
import type {
  Well,
  WellFilters,
  SectionFilters,
  WellSection,
  Substation,
  SubstationFilters,
  NearbyWellsParams,
  NearbyWellResult,
  BestPointParams,
  BestPoint,
  WellRanking,
  SubstationRanking,
  SubstationCandidate,
  PaginatedResponse,
  FilterOption,
} from "./types";
import { getAccessToken, refreshAccessToken, logout } from "./auth";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
});

// Attach the JWT to every request.
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On 401, try one silent refresh + retry; otherwise send the user to /login.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && original && !original._retried) {
      original._retried = true;
      const newToken = await refreshAccessToken();
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
      logout();
      if (typeof window !== "undefined") {
        window.location.href = `/login?next=${encodeURIComponent(
          window.location.pathname
        )}`;
      }
    }
    return Promise.reject(error);
  }
);

// ─── Wells ─────────────────────────────────────────────────────────────────

export async function fetchWells(
  filters: WellFilters = {},
  page = 1,
  pageSize = 100
): Promise<PaginatedResponse<Well>> {
  const { data } = await api.get<PaginatedResponse<Well>>("/wells/", {
    params: { ...filters, page, page_size: pageSize },
  });
  return data;
}

export async function fetchWell(id: number): Promise<Well> {
  const { data } = await api.get<Well>(`/wells/${id}/`);
  return data;
}

export async function fetchWellFilterOptions(): Promise<{
  statuses: FilterOption[];
  formats: FilterOption[];
  areas: FilterOption[];
}> {
  const { data } = await api.get("/wells/filter-options/");
  return data;
}

// ─── Sections ──────────────────────────────────────────────────────────────

export async function fetchSections(filters: SectionFilters = {}): Promise<WellSection[]> {
  const { data } = await api.get<WellSection[]>("/wells/sections/", { params: filters });
  return data;
}

// ─── Substations ───────────────────────────────────────────────────────────

export async function fetchSubstations(
  filters: SubstationFilters = {},
  page = 1,
  pageSize = 100
): Promise<PaginatedResponse<Substation>> {
  const { data } = await api.get<PaginatedResponse<Substation>>(
    "/substations/",
    { params: { ...filters, page, page_size: pageSize } }
  );
  return data;
}

export async function fetchSubstation(id: number): Promise<Substation> {
  const { data } = await api.get<Substation>(`/substations/${id}/`);
  return data;
}

export async function fetchSubstationFilterOptions(): Promise<{
  areas: FilterOption[];
}> {
  const { data } = await api.get("/substations/filter-options/");
  return data;
}

// ─── Nearby Wells ──────────────────────────────────────────────────────────

export async function fetchNearbyWells(
  params: NearbyWellsParams
): Promise<NearbyWellResult[]> {
  const { data } = await api.get<NearbyWellResult[]>("/wells/nearby/", {
    params,
  });
  return data;
}

// ─── Best Point ────────────────────────────────────────────────────────────

export async function fetchBestPoint(
  params: BestPointParams
): Promise<BestPoint[]> {
  const { data } = await api.post<BestPoint[]>("/analysis/best-point/", params);
  return data;
}

// ─── Rankings ──────────────────────────────────────────────────────────────

export async function fetchWellRankings(params?: {
  area?: string;
  limit?: number;
}): Promise<WellRanking[]> {
  const { data } = await api.get<WellRanking[]>("/wells/rankings/", {
    params,
  });
  return data;
}

export async function fetchSubstationRankings(params?: {
  area?: string;
  limit?: number;
}): Promise<SubstationRanking[]> {
  const { data } = await api.get<SubstationRanking[]>(
    "/substations/rankings/",
    { params }
  );
  return data;
}

export async function fetchSubstationCandidates(params?: {
  county?: string;
  min_wells?: number;
  limit?: number;
}): Promise<SubstationCandidate[]> {
  const { data } = await api.get<SubstationCandidate[]>(
    "/substations/candidates/",
    { params }
  );
  return data;
}

export default api;
