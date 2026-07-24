/**
 * Data Browser API — reads the real well tables from the Django backend
 * (see backend apps/wells/data_browser.py). Reuses the axios instance from
 * wells-backend (baseURL + JWT + array-param serialization).
 */
import api from "./wells-backend";

export interface BrowserColumn {
  name: string;
  type: string;
}

export interface BrowserTable {
  name: string;
  columns: BrowserColumn[];
}

export interface BrowserRowsResponse {
  table: string;
  columns: BrowserColumn[];
  results: Record<string, unknown>[];
  count: number;
  page: number;
  page_size: number;
}

export async function fetchBrowserTables(): Promise<BrowserTable[]> {
  const { data } = await api.get<{ tables: BrowserTable[] }>("/data-browser/tables/");
  return data.tables;
}

export interface BrowserRowsQuery {
  table: string;
  columns: string[];
  search?: string;
  page?: number;
  pageSize?: number;
}

export async function fetchBrowserRows(q: BrowserRowsQuery): Promise<BrowserRowsResponse> {
  const { data } = await api.get<BrowserRowsResponse>("/data-browser/rows/", {
    params: {
      table: q.table,
      columns: q.columns,
      search: q.search || undefined,
      page: q.page ?? 1,
      page_size: q.pageSize ?? 100,
    },
  });
  return data;
}
