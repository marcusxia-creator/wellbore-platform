"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import Papa from "papaparse";
import {
  Search,
  Pencil,
  Check,
  X,
  Trash2,
  Download,
  UploadCloud,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Database,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import { cn, formatNumber } from "@/lib/utils";
import type { Well } from "@/lib/types";
import { useImportedWells } from "@/lib/import/store";

const PAGE_SIZE = 50;

// ─── Column config ───────────────────────────────────────────────────────────

type ColType = "text" | "number" | "select" | "boolean";

interface Col {
  key: keyof Well;
  header: string;
  type: ColType;
  options?: string[];
  width?: string;
  format?: (v: unknown) => string;
}

const COLUMNS: Col[] = [
  { key: "uwi",                 header: "UWI",          type: "text", width: "min-w-[170px]" },
  { key: "area",                header: "Area",         type: "text" },
  { key: "well_status_text",    header: "Status",       type: "text", width: "min-w-[130px]" },
  { key: "well_status_group",   header: "Group",        type: "select", options: ["IDLE", "SUSP", "ABD"] },
  { key: "surf_latitude",       header: "Latitude",     type: "number", format: (v) => formatNumber(v as number, 5) },
  { key: "surf_longitude",      header: "Longitude",    type: "number", format: (v) => formatNumber(v as number, 5) },
  { key: "available_volume_m3", header: "Volume m³",    type: "number", format: (v) => formatNumber(v as number, 1) },
  { key: "burst_pressure_psi",  header: "Burst psi",    type: "number", format: (v) => formatNumber(v as number, 0) },
  { key: "format",              header: "Format",       type: "select", options: ["ATS", "NTS"] },
  { key: "strm",                header: "STRM",         type: "text" },
  { key: "horizontal_hole",     header: "Horiz.",       type: "boolean" },
  { key: "orphan",              header: "Orphan",       type: "boolean" },
];

const GROUP_BADGE: Record<string, string> = {
  IDLE: "bg-emerald-100 text-emerald-800",
  SUSP: "bg-amber-100 text-amber-800",
  ABD:  "bg-slate-200 text-slate-600",
};

// ─── Page ────────────────────────────────────────────────────────────────────

export default function DataBrowserPage() {
  const { rows, meta, loading, updateRow, deleteRows, clearAll } = useImportedWells();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [sortKey, setSortKey] = useState<keyof Well | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState<Partial<Well>>({});

  // ── Filter + sort + paginate ───────────────────────────────────────────────

  const filtered = useMemo(() => {
    let out = rows;
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      out = out.filter(
        (w) =>
          w.uwi.toLowerCase().includes(q) ||
          w.well_id.toLowerCase().includes(q) ||
          w.strm.toLowerCase().includes(q) ||
          w.area.toLowerCase().includes(q)
      );
    }
    if (statusFilter !== "ALL") out = out.filter((w) => w.well_status_group === statusFilter);
    if (sortKey) {
      out = [...out].sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey];
        if (av == null) return 1;
        if (bv == null) return -1;
        const cmp = av < bv ? -1 : av > bv ? 1 : 0;
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return out;
  }, [rows, search, statusFilter, sortKey, sortDir]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const pageRows = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  function handleSort(key: keyof Well) {
    if (sortKey === key) {
      if (sortDir === "asc") setSortDir("desc");
      else { setSortKey(null); setSortDir("asc"); }
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  // ── Editing ────────────────────────────────────────────────────────────────

  function startEdit(w: Well) {
    setEditingId(w.id);
    setDraft({ ...w });
  }

  function saveEdit() {
    if (editingId == null) return;
    const patch: Partial<Well> = { ...draft };
    for (const col of COLUMNS) {
      if (col.type === "number" && patch[col.key] != null) {
        const n = parseFloat(String(patch[col.key]));
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (patch as any)[col.key] = Number.isFinite(n) ? n : 0;
      }
    }
    updateRow(editingId, patch);
    setEditingId(null);
    setDraft({});
  }

  // ── Selection / delete ─────────────────────────────────────────────────────

  const allOnPageSelected = pageRows.length > 0 && pageRows.every((w) => selected.has(w.id));

  function toggleAllOnPage() {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allOnPageSelected) pageRows.forEach((w) => next.delete(w.id));
      else pageRows.forEach((w) => next.add(w.id));
      return next;
    });
  }

  function handleDeleteSelected() {
    if (selected.size === 0) return;
    if (!window.confirm(`Delete ${selected.size} selected well${selected.size > 1 ? "s" : ""}?`)) return;
    deleteRows([...selected]);
    setSelected(new Set());
  }

  function handleClearAll() {
    if (!window.confirm("Remove ALL imported data? This cannot be undone.")) return;
    clearAll();
    setSelected(new Set());
  }

  // ── Export ─────────────────────────────────────────────────────────────────

  function handleExport() {
    const csv = Papa.unparse(
      filtered.map((w) => ({
        Well_ID: w.well_id, UWI: w.uwi, Area: w.area,
        Surf_Latitude: w.surf_latitude, Surf_Longitude: w.surf_longitude,
        Well_Status_Text: w.well_status_text, Well_Status_Group: w.well_status_group,
        Available_Volume_m3: w.available_volume_m3,
        "Legal Subdivisions": w.legal_subdivisions,
        Section: w.section, Township: w.township, Range: w.range, Meridian: w.meridian,
        Crooked_Hole_TF: w.crooked_hole ? "T" : "F",
        Deviated_Hole_TF: w.deviated_hole ? "T" : "F",
        Horizontal_Hole_TF: w.horizontal_hole ? "T" : "F",
        Burst_Pressure_psi: w.burst_pressure_psi,
        Format: w.format, STRM: w.strm, orphan: w.orphan ? 1 : 0,
      }))
    );
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "wells-export.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Empty / loading states ─────────────────────────────────────────────────

  if (!loading && rows.length === 0) {
    return (
      <div>
        <PageHeader title="Data Browser" description="Browse and edit your imported well data." />
        <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed border-slate-300 bg-white px-6 py-20 text-center">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-slate-100">
            <Database size={26} className="text-slate-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">No imported data yet</p>
            <p className="mt-1 text-xs text-slate-500">
              Upload an Excel file on the Raw Data Import page to get started.
            </p>
          </div>
          <Link
            href="/raw-data-import"
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
          >
            <UploadCloud size={16} /> Go to Raw Data Import
          </Link>
        </div>
      </div>
    );
  }

  // ── Main table ─────────────────────────────────────────────────────────────

  return (
    <div>
      <PageHeader
        title="Data Browser"
        description={
          meta
            ? `${formatNumber(rows.length)} wells from ${meta.fileName} · imported ${new Date(meta.importedAt).toLocaleString()}`
            : `${formatNumber(rows.length)} imported wells`
        }
        actions={
          <>
            <button
              onClick={handleExport}
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Download size={14} /> Export CSV
            </button>
            <button
              onClick={handleClearAll}
              className="flex items-center gap-1.5 rounded-lg border border-red-200 bg-white px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
            >
              <Trash2 size={14} /> Clear all
            </button>
          </>
        }
      />

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search UWI, STRM, area…"
            className="w-64 rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-emerald-400 focus:outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 focus:border-emerald-400 focus:outline-none"
        >
          <option value="ALL">All statuses</option>
          <option value="IDLE">IDLE</option>
          <option value="SUSP">SUSP</option>
          <option value="ABD">ABD</option>
        </select>
        <span className="text-xs text-slate-500">
          {formatNumber(filtered.length)} of {formatNumber(rows.length)} wells
        </span>
        {selected.size > 0 && (
          <button
            onClick={handleDeleteSelected}
            className="ml-auto flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-2 text-xs font-medium text-white hover:bg-red-700 transition-colors"
          >
            <Trash2 size={14} /> Delete {selected.size} selected
          </button>
        )}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="w-10 px-3 py-3">
                  <input
                    type="checkbox"
                    checked={allOnPageSelected}
                    onChange={toggleAllOnPage}
                    className="accent-emerald-600"
                  />
                </th>
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    className={cn(
                      "cursor-pointer select-none whitespace-nowrap px-3 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-800",
                      col.width
                    )}
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.header}
                      {sortKey === col.key
                        ? sortDir === "asc" ? <ChevronUp size={13} /> : <ChevronDown size={13} />
                        : <ChevronsUpDown size={13} className="text-slate-300" />}
                    </span>
                  </th>
                ))}
                <th className="w-20 px-3 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={COLUMNS.length + 2} className="px-4 py-10 text-center text-sm text-slate-400">
                    Loading imported data…
                  </td>
                </tr>
              ) : pageRows.length === 0 ? (
                <tr>
                  <td colSpan={COLUMNS.length + 2} className="px-4 py-10 text-center text-sm text-slate-400">
                    No wells match your filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((w) => {
                  const isEditing = editingId === w.id;
                  return (
                    <tr
                      key={w.id}
                      className={cn(
                        "transition-colors",
                        isEditing ? "bg-emerald-50/60" : "hover:bg-slate-50",
                        selected.has(w.id) && !isEditing && "bg-emerald-50/30"
                      )}
                    >
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={selected.has(w.id)}
                          onChange={() =>
                            setSelected((prev) => {
                              const next = new Set(prev);
                              if (next.has(w.id)) next.delete(w.id);
                              else next.add(w.id);
                              return next;
                            })
                          }
                          className="accent-emerald-600"
                        />
                      </td>
                      {COLUMNS.map((col) => (
                        <td key={col.key} className="whitespace-nowrap px-3 py-2 text-slate-700">
                          {isEditing ? (
                            <EditCell
                              col={col}
                              value={draft[col.key]}
                              onChange={(v) => setDraft((d) => ({ ...d, [col.key]: v }))}
                            />
                          ) : (
                            <DisplayCell col={col} well={w} />
                          )}
                        </td>
                      ))}
                      <td className="px-3 py-2">
                        {isEditing ? (
                          <span className="flex items-center gap-1">
                            <button
                              onClick={saveEdit}
                              title="Save"
                              className="rounded-md p-1.5 text-emerald-600 hover:bg-emerald-100 transition-colors"
                            >
                              <Check size={15} />
                            </button>
                            <button
                              onClick={() => { setEditingId(null); setDraft({}); }}
                              title="Cancel"
                              className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 transition-colors"
                            >
                              <X size={15} />
                            </button>
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <button
                              onClick={() => startEdit(w)}
                              title="Edit row"
                              className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                            >
                              <Pencil size={14} />
                            </button>
                            <button
                              onClick={() => {
                                if (window.confirm(`Delete well ${w.uwi}?`)) deleteRows([w.id]);
                              }}
                              title="Delete row"
                              className="rounded-md p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                            >
                              <Trash2 size={14} />
                            </button>
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-slate-200 px-4 py-2.5">
          <p className="text-xs text-slate-500">
            Page {safePage} of {pageCount}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage <= 1}
              className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30 transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
              disabled={safePage >= pageCount}
              className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30 transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Cells ───────────────────────────────────────────────────────────────────

function DisplayCell({ col, well }: { col: Col; well: Well }) {
  const value = well[col.key];
  if (col.key === "well_status_group") {
    const v = String(value ?? "");
    return v ? (
      <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", GROUP_BADGE[v] ?? "bg-slate-100 text-slate-600")}>
        {v}
      </span>
    ) : <span className="text-slate-300">—</span>;
  }
  if (col.type === "boolean") {
    return value
      ? <Check size={15} className="text-emerald-600" />
      : <span className="text-slate-300">—</span>;
  }
  if (value == null || value === "") return <span className="text-slate-300">—</span>;
  return <>{col.format ? col.format(value) : String(value)}</>;
}

function EditCell({
  col,
  value,
  onChange,
}: {
  col: Col;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const base =
    "w-full rounded-md border border-emerald-300 bg-white px-2 py-1 text-xs text-slate-800 focus:border-emerald-500 focus:outline-none";

  if (col.type === "boolean") {
    return (
      <input
        type="checkbox"
        checked={Boolean(value)}
        onChange={(e) => onChange(e.target.checked)}
        className="accent-emerald-600"
      />
    );
  }
  if (col.type === "select") {
    return (
      <select value={String(value ?? "")} onChange={(e) => onChange(e.target.value)} className={base}>
        <option value="">—</option>
        {col.options?.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    );
  }
  return (
    <input
      type={col.type === "number" ? "number" : "text"}
      value={value == null ? "" : String(value)}
      onChange={(e) => onChange(e.target.value)}
      className={cn(base, col.type === "number" ? "min-w-[90px]" : "min-w-[110px]")}
    />
  );
}
