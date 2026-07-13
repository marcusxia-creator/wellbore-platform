"use client";

/**
 * Imported-wells store — holds well data uploaded on the Raw Data Import page
 * and persists it in IndexedDB so the Data Browser can read/edit it across
 * reloads. No backend required; swap the idb calls for API calls later.
 */
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from "react";
import type { Well } from "@/lib/types";
import { idbGet, idbSet, idbDel } from "./idb";

const ROWS_KEY = "imported-wells";
const META_KEY = "imported-meta";

export interface ImportMeta {
  fileName: string;
  sheetName: string;
  importedAt: string; // ISO
  sourceRowCount: number;
  skippedCount: number;
}

interface ImportedWellsStore {
  rows: Well[];
  meta: ImportMeta | null;
  loading: boolean;
  importData: (wells: Well[], meta: ImportMeta, mode: "replace" | "append") => void;
  updateRow: (id: number, patch: Partial<Well>) => void;
  deleteRows: (ids: number[]) => void;
  clearAll: () => void;
}

const Ctx = createContext<ImportedWellsStore | null>(null);

export function ImportedWellsProvider({ children }: { children: ReactNode }) {
  const [rows, setRows] = useState<Well[]>([]);
  const [meta, setMeta] = useState<ImportMeta | null>(null);
  const [loading, setLoading] = useState(true);

  // Hydrate from IndexedDB once on mount.
  useEffect(() => {
    let cancelled = false;
    Promise.all([idbGet<Well[]>(ROWS_KEY), idbGet<ImportMeta>(META_KEY)])
      .then(([r, m]) => {
        if (cancelled) return;
        if (r) setRows(r);
        if (m) setMeta(m);
      })
      .catch(() => {/* private-browsing or blocked IndexedDB — stay in-memory */})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const persist = useCallback((nextRows: Well[]) => {
    idbSet(ROWS_KEY, nextRows).catch(() => {});
  }, []);

  const importData = useCallback(
    (wells: Well[], newMeta: ImportMeta, mode: "replace" | "append") => {
      setRows((prev) => {
        let next: Well[];
        if (mode === "append") {
          const offset = prev.reduce((m, w) => Math.max(m, w.id), 0);
          next = [...prev, ...wells.map((w, i) => ({ ...w, id: offset + i + 1 }))];
        } else {
          next = wells;
        }
        persist(next);
        return next;
      });
      setMeta(newMeta);
      idbSet(META_KEY, newMeta).catch(() => {});
    },
    [persist]
  );

  const updateRow = useCallback((id: number, patch: Partial<Well>) => {
    setRows((prev) => {
      const next = prev.map((w) => (w.id === id ? { ...w, ...patch, id } : w));
      persist(next);
      return next;
    });
  }, [persist]);

  const deleteRows = useCallback((ids: number[]) => {
    const idSet = new Set(ids);
    setRows((prev) => {
      const next = prev.filter((w) => !idSet.has(w.id));
      persist(next);
      return next;
    });
  }, [persist]);

  const clearAll = useCallback(() => {
    setRows([]);
    setMeta(null);
    idbDel(ROWS_KEY).catch(() => {});
    idbDel(META_KEY).catch(() => {});
  }, []);

  const ctx = useMemo(
    () => ({ rows, meta, loading, importData, updateRow, deleteRows, clearAll }),
    [rows, meta, loading, importData, updateRow, deleteRows, clearAll]
  );

  return <Ctx.Provider value={ctx}>{children}</Ctx.Provider>;
}

export function useImportedWells(): ImportedWellsStore {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useImportedWells must be used inside <ImportedWellsProvider>");
  return ctx;
}
