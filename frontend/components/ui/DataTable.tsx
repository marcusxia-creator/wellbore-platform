"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

// Use `object` as the base constraint — wide enough for any row type,
// but still lets TypeScript infer specific shapes in render callbacks.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface Column<T = any> {
  key: keyof T | string;
  header: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
interface DataTableProps<T = any> {
  columns: Column<T>[];
  data: T[];
  keyField: keyof T;
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  className?: string;
}

type SortDir = "asc" | "desc" | null;

export default function DataTable<T>({
  columns,
  data,
  keyField,
  loading,
  emptyMessage = "No data found.",
  onRowClick,
  className,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);

  function handleSort(key: string) {
    if (sortKey === key) {
      const next = sortDir === "asc" ? "desc" : sortDir === "desc" ? null : "asc";
      setSortDir(next);
      if (next === null) setSortKey(null);
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  const sorted = [...data].sort((a, b) => {
    if (!sortKey || !sortDir) return 0;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const av = (a as any)[sortKey];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const bv = (b as any)[sortKey];
    if (av == null) return 1;
    if (bv == null) return -1;
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === "asc" ? cmp : -cmp;
  });

  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm", className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {columns.map((col) => (
                <th
                  key={String(col.key)}
                  className={cn(
                    "px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap",
                    col.sortable && "cursor-pointer select-none hover:text-slate-800",
                    col.className
                  )}
                  onClick={() => col.sortable && handleSort(String(col.key))}
                >
                  <span className="flex items-center gap-1">
                    {col.header}
                    {col.sortable && (
                      <span className="text-slate-400">
                        {sortKey === col.key && sortDir === "asc" ? (
                          <ChevronUp size={13} />
                        ) : sortKey === col.key && sortDir === "desc" ? (
                          <ChevronDown size={13} />
                        ) : (
                          <ChevronsUpDown size={13} />
                        )}
                      </span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-slate-400">
                  <div className="flex items-center justify-center gap-2">
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
                    Loading…
                  </div>
                </td>
              </tr>
            ) : sorted.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-12 text-center text-slate-400">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              sorted.map((row, idx) => (
                <tr
                  key={String((row as Record<string, unknown>)[String(keyField)] ?? idx)}
                  onClick={() => onRowClick?.(row)}
                  className={cn(
                    "hover:bg-slate-50 transition-colors",
                    onRowClick && "cursor-pointer"
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={String(col.key)}
                      className={cn("px-4 py-3 text-slate-700 whitespace-nowrap", col.className)}
                    >
                      {col.render
                        ? col.render(row)
                        : String((row as Record<string, unknown>)[String(col.key)] ?? "—")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
