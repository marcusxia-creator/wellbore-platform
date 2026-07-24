"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Search,
  ChevronLeft,
  ChevronRight,
  Columns3,
  Database,
  TableProperties,
  AlertTriangle,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import { cn, formatNumber } from "@/lib/utils";
import {
  fetchBrowserTables,
  fetchBrowserRows,
  type BrowserTable,
  type BrowserColumn,
} from "@/lib/data-browser";

const PAGE_SIZE_OPTIONS = [25, 50, 100, 250, 500];
const DEFAULT_COLUMN_COUNT = 12;

function cellText(value: unknown): string {
  if (value == null || value === "") return "—";
  return String(value);
}

export default function DataBrowserPage() {
  // Catalog
  const [tables, setTables] = useState<BrowserTable[]>([]);
  const [loadingCatalog, setLoadingCatalog] = useState(true);

  // Selection
  const [tableName, setTableName] = useState("");
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);

  // Results
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [resultColumns, setResultColumns] = useState<BrowserColumn[]>([]);
  const [count, setCount] = useState(0);
  const [loadingRows, setLoadingRows] = useState(false);
  const [error, setError] = useState("");
  const reqId = useRef(0);

  const activeTable = useMemo(
    () => tables.find((t) => t.name === tableName),
    [tables, tableName]
  );
  const columns = activeTable?.columns ?? [];

  // Load catalog once.
  useEffect(() => {
    fetchBrowserTables()
      .then((catalog) => {
        setTables(catalog);
        if (catalog[0]) setTableName(catalog[0].name);
        setError("");
      })
      .catch(() =>
        // The backend Data Browser API is not built yet — see the handoff spec
        // in docs/backend-api-spec.md. TODO: remove this note once it's live.
        setError(
          "Data Browser backend is not available yet. The GET /api/data-browser/tables/ endpoint is pending (see docs/backend-api-spec.md)."
        )
      )
      .finally(() => setLoadingCatalog(false));
  }, []);

  // Reset column selection / paging when the table changes.
  useEffect(() => {
    if (!activeTable) {
      setSelectedColumns([]);
      return;
    }
    setSelectedColumns(activeTable.columns.slice(0, DEFAULT_COLUMN_COUNT).map((c) => c.name));
    setPage(1);
    setSearch("");
    setSearchInput("");
  }, [activeTable]);

  // Fetch rows when table / columns / search / paging change.
  useEffect(() => {
    if (!tableName || selectedColumns.length === 0) {
      setRows([]);
      setResultColumns([]);
      setCount(0);
      return;
    }
    const id = ++reqId.current;
    setLoadingRows(true);
    fetchBrowserRows({ table: tableName, columns: selectedColumns, search, page, pageSize })
      .then((data) => {
        if (id !== reqId.current) return;
        setRows(data.results);
        setResultColumns(data.columns);
        setCount(data.count);
        setError("");
      })
      .catch((e) => {
        if (id !== reqId.current) return;
        setError(e?.message || "Unable to query the selected table.");
        setRows([]);
      })
      .finally(() => {
        if (id === reqId.current) setLoadingRows(false);
      });
  }, [tableName, selectedColumns, search, page, pageSize]);

  function toggleColumn(name: string) {
    setSelectedColumns((current) => {
      if (current.includes(name)) {
        return current.length === 1 ? current : current.filter((c) => c !== name);
      }
      return [...current, name];
    });
    setPage(1);
  }

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  }

  const pageCount = Math.max(1, Math.ceil(count / pageSize));
  const firstRow = count === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastRow = Math.min(page * pageSize, count);

  return (
    <div>
      <PageHeader
        title="Data Browser"
        description="Browse the imported well tables — pick a table, choose columns, search, and page through the rows."
      />

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertTriangle size={16} className="shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        {/* Sidebar controls */}
        <aside className="flex flex-col gap-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <label className="mb-1 block text-xs font-medium text-slate-500">Table</label>
            <select
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              disabled={loadingCatalog || tables.length === 0}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-400 focus:outline-none"
            >
              {tables.map((t) => (
                <option key={t.name} value={t.name}>{t.name}</option>
              ))}
            </select>

            <form onSubmit={submitSearch} className="mt-4">
              <label className="mb-1 block text-xs font-medium text-slate-500">Search values</label>
              <div className="relative">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Find any value…"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-emerald-400 focus:outline-none"
                />
              </div>
              <button
                type="submit"
                className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
              >
                <Search size={15} /> Query table
              </button>
            </form>

            <label className="mb-1 mt-4 block text-xs font-medium text-slate-500">Rows per page</label>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 focus:border-emerald-400 focus:outline-none"
            >
              {PAGE_SIZE_OPTIONS.map((n) => (
                <option key={n} value={n}>{n} rows</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-xl border border-slate-200 bg-white px-2 py-2.5 text-center shadow-sm">
              <p className="text-lg font-semibold text-slate-900">{tables.length}</p>
              <p className="text-[11px] text-slate-500">Tables</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white px-2 py-2.5 text-center shadow-sm">
              <p className="text-lg font-semibold text-slate-900">{columns.length}</p>
              <p className="text-[11px] text-slate-500">Columns</p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white px-2 py-2.5 text-center shadow-sm">
              <p className="text-lg font-semibold text-slate-900">{formatNumber(count)}</p>
              <p className="text-[11px] text-slate-500">Rows</p>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <section className="min-w-0 space-y-4">
          {/* Column chips */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Columns3 size={16} /> Columns
              <span className="text-xs font-normal text-slate-400">
                ({selectedColumns.length}/{columns.length} shown — click to toggle)
              </span>
            </div>
            <div className="flex max-h-40 flex-wrap gap-1.5 overflow-y-auto">
              {columns.map((col) => {
                const on = selectedColumns.includes(col.name);
                return (
                  <button
                    key={col.name}
                    type="button"
                    onClick={() => toggleColumn(col.name)}
                    title={`${col.name} (${col.type})`}
                    className={cn(
                      "rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors",
                      on
                        ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                        : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
                    )}
                  >
                    {col.name}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Table */}
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2.5">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <TableProperties size={16} /> {tableName || "Select a table"}
              </div>
              <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                <Database size={13} />
                {loadingRows
                  ? "Loading…"
                  : `${formatNumber(firstRow)}–${formatNumber(lastRow)} of ${formatNumber(count)}`}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50">
                  <tr>
                    {resultColumns.map((col) => (
                      <th key={col.name} className="whitespace-nowrap px-3 py-2 font-semibold text-slate-600">
                        {col.name}
                        <span className="ml-1 font-normal text-slate-400">{col.type}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {loadingRows ? (
                    <tr>
                      <td colSpan={Math.max(resultColumns.length, 1)} className="px-4 py-10 text-center text-slate-400">
                        Loading rows…
                      </td>
                    </tr>
                  ) : rows.length === 0 ? (
                    <tr>
                      <td colSpan={Math.max(resultColumns.length, 1)} className="px-4 py-10 text-center text-slate-400">
                        No rows match the current query.
                      </td>
                    </tr>
                  ) : (
                    rows.map((row, i) => (
                      <tr key={`${page}-${i}`} className="hover:bg-slate-50">
                        {resultColumns.map((col) => (
                          <td
                            key={col.name}
                            title={cellText(row[col.name])}
                            className="max-w-[280px] truncate whitespace-nowrap px-3 py-1.5 text-slate-700"
                          >
                            {cellText(row[col.name])}
                          </td>
                        ))}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-slate-200 px-4 py-2.5">
              <p className="text-xs text-slate-500">Page {page} of {formatNumber(pageCount)}</p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || loadingRows}
                  className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-30 transition-colors"
                >
                  <ChevronLeft size={14} /> Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
                  disabled={lastRow >= count || loadingRows}
                  className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-30 transition-colors"
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
