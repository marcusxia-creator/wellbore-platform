"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import Link from "next/link";
import * as XLSX from "xlsx";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  X,
  Table2,
  ArrowRight,
} from "lucide-react";
import PageHeader from "@/components/layout/PageHeader";
import { cn, formatNumber } from "@/lib/utils";
import {
  WELL_FIELDS,
  autoMapColumns,
  buildWells,
  type ColumnMapping,
} from "@/lib/import/fields";
import { useImportedWells } from "@/lib/import/store";

const ACCEPTED = [".xlsx", ".xls", ".csv"];
const PREVIEW_ROWS = 8;

interface ParsedFile {
  fileName: string;
  workbook: XLSX.WorkBook;
}

interface SheetData {
  headers: string[];
  rows: Record<string, unknown>[];
}

function readSheet(wb: XLSX.WorkBook, sheetName: string): SheetData {
  const ws = wb.Sheets[sheetName];
  if (!ws) return { headers: [], rows: [] };
  const matrix = XLSX.utils.sheet_to_json<unknown[]>(ws, { header: 1, defval: null });
  const headers = (matrix[0] ?? []).map((h) => String(h ?? "").trim()).filter(Boolean);
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(ws, { defval: null });
  return { headers, rows };
}

export default function RawDataImportPage() {
  const { rows: existingRows, meta, importData } = useImportedWells();

  const [parsed, setParsed] = useState<ParsedFile | null>(null);
  const [sheetName, setSheetName] = useState<string>("");
  const [mapping, setMapping] = useState<ColumnMapping>({});
  const [mode, setMode] = useState<"replace" | "append">("replace");
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsing, setParsing] = useState(false);
  const [done, setDone] = useState<{ imported: number; skipped: number } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // ── File handling ──────────────────────────────────────────────────────────

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setDone(null);
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setError(`Unsupported file type "${ext}". Accepted: ${ACCEPTED.join(", ")}`);
      return;
    }
    setParsing(true);
    try {
      const buf = await file.arrayBuffer();
      const wb = XLSX.read(buf);
      const first = wb.SheetNames[0];
      if (!first) throw new Error("No sheets found in file.");
      setParsed({ fileName: file.name, workbook: wb });
      setSheetName(first);
      setMapping(autoMapColumns(readSheet(wb, first).headers));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse file.");
      setParsed(null);
    } finally {
      setParsing(false);
    }
  }, []);

  function handleSheetChange(name: string) {
    if (!parsed) return;
    setSheetName(name);
    setMapping(autoMapColumns(readSheet(parsed.workbook, name).headers));
  }

  function resetAll() {
    setParsed(null);
    setSheetName("");
    setMapping({});
    setDone(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  // ── Derived preview / validation ───────────────────────────────────────────

  const sheet = useMemo<SheetData>(
    () => (parsed ? readSheet(parsed.workbook, sheetName) : { headers: [], rows: [] }),
    [parsed, sheetName]
  );

  const result = useMemo(
    () => (sheet.rows.length ? buildWells(sheet.rows, mapping) : null),
    [sheet, mapping]
  );

  const requiredMissing = useMemo(() => {
    const mapped = new Set(Object.values(mapping).filter(Boolean));
    return WELL_FIELDS.filter((f) => f.required && !mapped.has(f.key));
  }, [mapping]);

  function handleImport() {
    if (!parsed || !result) return;
    importData(
      result.wells,
      {
        fileName: parsed.fileName,
        sheetName,
        importedAt: new Date().toISOString(),
        sourceRowCount: sheet.rows.length,
        skippedCount: result.skipped.length,
      },
      mode
    );
    setDone({ imported: result.wells.length, skipped: result.skipped.length });
    setParsed(null);
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div>
      <PageHeader
        title="Raw Data Import"
        description="Upload an Excel or CSV file of oil well data, review the column mapping, and import it."
      />

      {/* Current dataset banner */}
      {existingRows.length > 0 && !done && (
        <div className="mb-4 flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <FileSpreadsheet size={18} className="shrink-0 text-emerald-600" />
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-900">{formatNumber(existingRows.length)}</span>{" "}
            wells currently imported
            {meta && (
              <>
                {" "}from <span className="font-medium">{meta.fileName}</span> on{" "}
                {new Date(meta.importedAt).toLocaleDateString()}
              </>
            )}
            .
          </p>
          <Link
            href="/data-browser"
            className="ml-auto flex shrink-0 items-center gap-1 text-sm font-medium text-emerald-700 hover:text-emerald-900 transition-colors"
          >
            Browse data <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {/* Success state */}
      {done && (
        <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 size={22} className="shrink-0 text-emerald-600" />
            <div>
              <p className="text-sm font-semibold text-emerald-900">
                Imported {formatNumber(done.imported)} wells
                {done.skipped > 0 && ` (${formatNumber(done.skipped)} rows skipped)`}
              </p>
              <p className="mt-0.5 text-xs text-emerald-700">
                The data is saved in your browser and ready to review.
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <button
                onClick={resetAll}
                className="rounded-lg border border-emerald-300 px-3 py-1.5 text-xs font-medium text-emerald-800 hover:bg-emerald-100 transition-colors"
              >
                Import another file
              </button>
              <Link
                href="/data-browser"
                className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
              >
                <Table2 size={14} /> Open Data Browser
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          <AlertTriangle size={16} className="shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-800">
            <X size={15} />
          </button>
        </div>
      )}

      {/* Upload zone */}
      {!parsed && (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const file = e.dataTransfer.files?.[0];
            if (file) handleFile(file);
          }}
          onClick={() => inputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-16 text-center transition-colors",
            dragOver
              ? "border-emerald-400 bg-emerald-50"
              : "border-slate-300 bg-white hover:border-emerald-300 hover:bg-slate-50"
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(",")}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-emerald-100">
            <UploadCloud size={26} className="text-emerald-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">
              {parsing ? "Parsing file…" : "Drop your Excel file here, or click to browse"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Supports {ACCEPTED.join(", ")} — headers are auto-mapped to well fields
            </p>
          </div>
        </div>
      )}

      {/* Mapping + preview */}
      {parsed && (
        <div className="space-y-4">
          {/* File bar */}
          <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
            <FileSpreadsheet size={18} className="shrink-0 text-emerald-600" />
            <p className="truncate text-sm font-medium text-slate-800">{parsed.fileName}</p>
            {parsed.workbook.SheetNames.length > 1 && (
              <select
                value={sheetName}
                onChange={(e) => handleSheetChange(e.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700"
              >
                {parsed.workbook.SheetNames.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            )}
            <span className="text-xs text-slate-500">
              {formatNumber(sheet.rows.length)} rows · {sheet.headers.length} columns
            </span>
            <button
              onClick={resetAll}
              className="ml-auto flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors"
            >
              <X size={14} /> Remove
            </button>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[380px_1fr]">
            {/* Column mapping */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 px-4 py-3">
                <h2 className="text-sm font-semibold text-slate-800">Column Mapping</h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  Match spreadsheet columns to well fields. Unmapped columns are ignored.
                </p>
              </div>
              <div className="max-h-[420px] overflow-y-auto p-3">
                <ul className="space-y-1.5">
                  {sheet.headers.map((header) => (
                    <li key={header} className="flex items-center gap-2">
                      <span className="w-36 shrink-0 truncate text-xs font-medium text-slate-700" title={header}>
                        {header}
                      </span>
                      <ArrowRight size={12} className="shrink-0 text-slate-400" />
                      <select
                        value={mapping[header] ?? ""}
                        onChange={(e) => setMapping((m) => ({ ...m, [header]: e.target.value }))}
                        className={cn(
                          "min-w-0 flex-1 rounded-lg border px-2 py-1.5 text-xs",
                          mapping[header]
                            ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                            : "border-slate-300 bg-white text-slate-500"
                        )}
                      >
                        <option value="">— Ignore —</option>
                        {WELL_FIELDS.map((f) => (
                          <option
                            key={f.key}
                            value={f.key}
                            disabled={Object.entries(mapping).some(([h, k]) => k === f.key && h !== header)}
                          >
                            {f.label}{f.required ? " *" : ""}
                          </option>
                        ))}
                      </select>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Validation + preview + import */}
            <div className="min-w-0 space-y-4">
              {/* Validation summary */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm">
                  <p className="text-xs font-medium text-slate-500">Valid rows</p>
                  <p className="mt-1 text-xl font-semibold text-emerald-700">
                    {result ? formatNumber(result.wells.length) : "—"}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm">
                  <p className="text-xs font-medium text-slate-500">Skipped rows</p>
                  <p className={cn(
                    "mt-1 text-xl font-semibold",
                    result && result.skipped.length > 0 ? "text-amber-600" : "text-slate-900"
                  )}>
                    {result ? formatNumber(result.skipped.length) : "—"}
                  </p>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm">
                  <p className="text-xs font-medium text-slate-500">Mapped columns</p>
                  <p className="mt-1 text-xl font-semibold text-slate-900">
                    {Object.values(mapping).filter(Boolean).length}/{sheet.headers.length}
                  </p>
                </div>
              </div>

              {/* Required fields warning */}
              {requiredMissing.length > 0 && (
                <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                  <p>
                    Required field{requiredMissing.length > 1 ? "s" : ""} not mapped:{" "}
                    <span className="font-semibold">
                      {requiredMissing.map((f) => f.label).join(", ")}
                    </span>
                    . Rows will be skipped without them.
                  </p>
                </div>
              )}

              {/* Skip reasons */}
              {result && result.skipped.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <p className="text-xs font-semibold text-slate-700">
                    First skipped rows ({formatNumber(result.skipped.length)} total)
                  </p>
                  <ul className="mt-1.5 space-y-0.5 text-xs text-slate-500">
                    {result.skipped.slice(0, 5).map((s) => (
                      <li key={s.rowNumber}>Row {s.rowNumber}: {s.reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Preview table */}
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 px-4 py-3">
                  <h2 className="text-sm font-semibold text-slate-800">
                    Preview <span className="font-normal text-slate-400">(first {PREVIEW_ROWS} rows)</span>
                  </h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-200 bg-slate-50">
                      <tr>
                        {sheet.headers.map((h) => (
                          <th key={h} className="whitespace-nowrap px-3 py-2 font-semibold text-slate-500">
                            <span className={cn(!mapping[h] && "opacity-40 line-through")}>{h}</span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {sheet.rows.slice(0, PREVIEW_ROWS).map((row, i) => (
                        <tr key={i}>
                          {sheet.headers.map((h) => (
                            <td
                              key={h}
                              className={cn(
                                "whitespace-nowrap px-3 py-1.5 text-slate-700",
                                !mapping[h] && "text-slate-300"
                              )}
                            >
                              {row[h] == null || row[h] === "" ? "—" : String(row[h])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Import controls */}
              <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
                {existingRows.length > 0 && (
                  <div className="flex items-center gap-3 text-xs text-slate-600">
                    <label className="flex cursor-pointer items-center gap-1.5">
                      <input
                        type="radio"
                        checked={mode === "replace"}
                        onChange={() => setMode("replace")}
                        className="accent-emerald-600"
                      />
                      Replace existing data
                    </label>
                    <label className="flex cursor-pointer items-center gap-1.5">
                      <input
                        type="radio"
                        checked={mode === "append"}
                        onChange={() => setMode("append")}
                        className="accent-emerald-600"
                      />
                      Append to existing
                    </label>
                  </div>
                )}
                <button
                  onClick={handleImport}
                  disabled={!result || result.wells.length === 0}
                  className={cn(
                    "ml-auto flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors",
                    result && result.wells.length > 0
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "cursor-not-allowed bg-slate-300"
                  )}
                >
                  <UploadCloud size={16} />
                  Import {result ? formatNumber(result.wells.length) : 0} wells
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
