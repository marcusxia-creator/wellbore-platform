"use client";

import { createContext, useContext, useMemo, type ReactNode } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface WellsStore {
  wellsLoading: boolean;
}

// ── Context ───────────────────────────────────────────────────────────────────

const WellsContext = createContext<WellsStore | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────
//
// The Wells page fetches its own data straight from the Django backend
// (see `lib/wells-backend.ts`). This provider is a lightweight, non-blocking
// shim kept only so `LoadingGate` has a store to read; it never blocks.

export function WellsProvider({ children }: { children: ReactNode }) {
  const ctx = useMemo<WellsStore>(() => ({ wellsLoading: false }), []);
  return <WellsContext.Provider value={ctx}>{children}</WellsContext.Provider>;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useWellsStore(): WellsStore {
  const ctx = useContext(WellsContext);
  if (!ctx) throw new Error("useWellsStore must be used inside <WellsProvider>");
  return ctx;
}
