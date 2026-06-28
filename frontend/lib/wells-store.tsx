"use client";

import { createContext, useContext, useState, useEffect, useRef, useCallback, useMemo, type ReactNode } from "react";
import type { Well, WellSection, SectionFilters } from "./types";
import { fetchWells, fetchSections } from "./api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface WellsStore {
  allWells: Well[];
  wellsLoading: boolean;
  /** Returns cached sections for the given filters, fetching if not yet cached. */
  getSections: (filters: SectionFilters) => Promise<WellSection[]>;
}

// ── Context ───────────────────────────────────────────────────────────────────

const WellsContext = createContext<WellsStore | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function WellsProvider({ children }: { children: ReactNode }) {
  const [allWells, setAllWells]       = useState<Well[]>([]);
  const [wellsLoading, setWellsLoading] = useState(true);

  // Section cache: filter key → WellSection[]. Lives for the full session.
  const sectionCache = useRef(new Map<string, WellSection[]>());
  // In-flight promises: prevent duplicate fetches for the same key.
  const inflight = useRef(new Map<string, Promise<WellSection[]>>());

  // ── Fetch all wells once ───────────────────────────────────────────────────

  useEffect(() => {
    const PAGE_SIZE = 1000;
    let cancelled = false;

    async function load() {
      try {
        const first = await fetchWells({}, 1, PAGE_SIZE);
        if (cancelled) return;

        const pageCount = Math.ceil(first.count / PAGE_SIZE);
        if (pageCount <= 1) { setAllWells(first.results); return; }

        const rest = await Promise.all(
          Array.from({ length: pageCount - 1 }, (_, i) =>
            fetchWells({}, i + 2, PAGE_SIZE).then((r) => r.results)
          )
        );
        if (!cancelled) setAllWells([...first.results, ...rest.flat()]);
      } catch {
        setAllWells([]);
      } finally {
        if (!cancelled) setWellsLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  // ── Section fetcher with cache ─────────────────────────────────────────────

  const getSections = useCallback(async (filters: SectionFilters): Promise<WellSection[]> => {
    const key = JSON.stringify(filters);

    if (sectionCache.current.has(key)) return sectionCache.current.get(key)!;

    // Reuse an in-flight request for the same key
    if (inflight.current.has(key)) return inflight.current.get(key)!;

    const promise = fetchSections(filters).then((data) => {
      sectionCache.current.set(key, data);
      inflight.current.delete(key);
      return data;
    });

    inflight.current.set(key, promise);
    return promise;
  }, []); // only uses refs — stable for the lifetime of the provider

  const ctx = useMemo(
    () => ({ allWells, wellsLoading, getSections }),
    [allWells, wellsLoading, getSections]
  );

  return (
    <WellsContext.Provider value={ctx}>
      {children}
    </WellsContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useWellsStore(): WellsStore {
  const ctx = useContext(WellsContext);
  if (!ctx) throw new Error("useWellsStore must be used inside <WellsProvider>");
  return ctx;
}
