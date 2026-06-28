"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Layers,
  Zap,
  MapPin,
  Target,
  BarChart2,
  Award,
  PlusCircle,
  ChevronLeft,
  ChevronRight,
  Drill,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/wells", label: "Wells", icon: Drill },
  { href: "/substations", label: "Substations", icon: Zap },
  { href: "/nearby-wells", label: "Nearby Wells", icon: MapPin },
  { href: "/best-point", label: "Best Point", icon: Target },
  { href: "/well-ranking", label: "Well Ranking", icon: BarChart2 },
  { href: "/substation-ranking", label: "Substation Ranking", icon: Award },
  { href: "/substation-candidates", label: "Sub. Candidates", icon: PlusCircle },
] as const;

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "relative flex flex-col bg-slate-900 text-slate-100 transition-all duration-300 ease-in-out h-screen sticky top-0 shrink-0",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-700">
        <Layers className="shrink-0 text-emerald-400" size={22} />
        {!collapsed && (
          <span className="font-semibold text-base tracking-tight text-white">
            WellScout
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 space-y-1 px-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-emerald-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              <Icon size={18} className="shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed((c) => !c)}
        className="absolute -right-3 top-16 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white shadow-md transition-colors"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </aside>
  );
}
