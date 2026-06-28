import { cn } from "@/lib/utils";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type IconComponent = React.ComponentType<any>;

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: IconComponent;
  trend?: { value: number; label: string };
  className?: string;
}

export default function StatCard({ label, value, icon: Icon, trend, className }: StatCardProps) {
  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white p-5 shadow-sm", className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {Icon && (
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
            <Icon size={18} />
          </span>
        )}
      </div>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      {trend && (
        <p className={cn("mt-1 text-xs font-medium", trend.value >= 0 ? "text-emerald-600" : "text-red-500")}>
          {trend.value >= 0 ? "+" : ""}{trend.value}% {trend.label}
        </p>
      )}
    </div>
  );
}
