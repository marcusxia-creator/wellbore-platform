"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useSyncExternalStore } from "react";
import {
  Zap,
  MapPin,
  Target,
  BarChart2,
  Award,
  PlusCircle,
  ChevronLeft,
  ChevronRight,
  Drill,
  Gauge,
  LogOut,
  UploadCloud,
  Table2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getStoredUsername, logout } from "@/lib/auth";
// Sidebar uses warm "stone" neutrals (not cool stone) to harmonize with the
// page's warm cream background (#f8f7f2).

const NAV_ITEMS = [
  { href: "/wells", label: "Wells", icon: Drill },
  { href: "/substations", label: "Substations", icon: Zap },
  { href: "/nearby-wells", label: "Nearby Wells", icon: MapPin },
  { href: "/best-point", label: "Best Point", icon: Target },
  { href: "/well-ranking", label: "Well Ranking", icon: BarChart2 },
  { href: "/substation-ranking", label: "Substation Ranking", icon: Award },
  { href: "/substation-candidates", label: "Sub. Candidates", icon: PlusCircle },
  { href: "/raw-data-import", label: "Raw Data Import", icon: UploadCloud },
  { href: "/data-browser", label: "Data Browser", icon: Table2 },
] as const;

const IS_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

const subscribeNoop = () => () => {};
const getServerUsername = () => null;

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);

  // Read from cookie client-side only (server snapshot is null) to avoid a
  // server/client hydration mismatch.
  const username = useSyncExternalStore(
    subscribeNoop,
    getStoredUsername,
    getServerUsername
  );

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  return (
    <aside
      className={cn(
        "sticky top-0 z-20 flex h-screen shrink-0 flex-col text-stone-300",
        "bg-gradient-to-b from-stone-900 to-stone-950 border-r border-white/5",
        "transition-[width] duration-300 ease-in-out",
        collapsed ? "w-[68px]" : "w-60"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex h-16 items-center gap-3 border-b border-white/5 px-4",
          collapsed && "justify-center px-0"
        )}
      >
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-lg shadow-emerald-900/40">
          <Gauge className="text-white" size={20} />
        </div>
        {!collapsed && (
          <div className="leading-tight">
            <p className="text-[15px] font-semibold tracking-tight text-white">
              WellScout
            </p>
            <p className="text-[11px] text-stone-400">Terralog Technologies</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {!collapsed && (
          <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-stone-500">
            Menu
          </p>
        )}
        <ul className="space-y-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <li key={href}>
                <Link
                  href={href}
                  title={collapsed ? label : undefined}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    collapsed && "justify-center px-0",
                    active
                      ? "bg-emerald-500/10 text-white"
                      : "text-stone-400 hover:bg-white/5 hover:text-stone-100"
                  )}
                >
                  {active && (
                    <span className="absolute left-0 top-1/2 h-5 w-1 -transtone-y-1/2 rounded-r-full bg-emerald-400" />
                  )}
                  <Icon
                    size={18}
                    className={cn(
                      "shrink-0 transition-colors",
                      active
                        ? "text-emerald-400"
                        : "text-stone-500 group-hover:text-stone-200"
                    )}
                  />
                  {!collapsed && <span className="truncate">{label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer: user + status + collapse */}
      <div className="border-t border-white/5 p-3">
        {username && (
          <div
            className={cn(
              "mb-1 flex items-center gap-2 rounded-lg px-2 py-1.5",
              collapsed && "justify-center px-0"
            )}
            title={username}
          >
            <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-emerald-500/15 text-[11px] font-semibold uppercase text-emerald-400">
              {username.charAt(0)}
            </span>
            {!collapsed && (
              <span className="truncate text-xs font-medium text-stone-300">
                {username}
              </span>
            )}
          </div>
        )}
        <button
          onClick={handleLogout}
          title={collapsed ? "Sign out" : undefined}
          className={cn(
            "mb-1 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-stone-400 transition-colors hover:bg-white/5 hover:text-stone-100",
            collapsed && "justify-center px-0"
          )}
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span>Sign out</span>}
        </button>
        <div
          className={cn(
            "mb-2 flex items-center gap-2 px-2 text-[11px] text-stone-500",
            collapsed && "justify-center px-0"
          )}
        >
          <span
            className={cn(
              "h-2 w-2 shrink-0 rounded-full",
              IS_MOCK ? "bg-amber-400" : "bg-emerald-500"
            )}
          />
          {!collapsed && <span>{IS_MOCK ? "Demo data" : "Live data"}</span>}
        </div>
        <button
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-stone-400 transition-colors hover:bg-white/5 hover:text-stone-100",
            collapsed && "justify-center px-0"
          )}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
