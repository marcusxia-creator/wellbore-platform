"use client";

import { useWellsStore } from "@/lib/wells-store";

export default function LoadingGate({ children }: { children: React.ReactNode }) {
  const { wellsLoading } = useWellsStore();

  if (wellsLoading) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-5">
        <div className="relative h-14 w-14">
          <div className="absolute inset-0 rounded-full border-4 border-slate-200" />
          <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-emerald-600" />
        </div>
        <div className="text-center">
          <p className="text-sm font-semibold text-slate-700">Loading wellbore data</p>
          <p className="mt-1 text-xs text-slate-400">Fetching wells from the backend…</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
