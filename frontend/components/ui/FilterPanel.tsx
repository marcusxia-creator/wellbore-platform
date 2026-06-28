"use client";

import { Search, SlidersHorizontal, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SelectFilterProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}

export function SelectFilter({ label, value, onChange, options }: SelectFilterProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-slate-500">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

interface RangeFilterProps {
  label: string;
  min: string;
  max: string;
  onMinChange: (v: string) => void;
  onMaxChange: (v: string) => void;
  placeholder?: { min?: string; max?: string };
}

export function RangeFilter({ label, min, max, onMinChange, onMaxChange, placeholder }: RangeFilterProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-slate-500">{label}</label>
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={min}
          onChange={(e) => onMinChange(e.target.value)}
          placeholder={placeholder?.min ?? "Min"}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
        <span className="text-slate-400 text-sm">–</span>
        <input
          type="number"
          value={max}
          onChange={(e) => onMaxChange(e.target.value)}
          placeholder={placeholder?.max ?? "Max"}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>
    </div>
  );
}

interface SearchInputProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}

export function SearchInput({ value, onChange, placeholder = "Search…" }: SearchInputProps) {
  return (
    <div className="relative">
      <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-8 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
      />
      {value && (
        <button
          onClick={() => onChange("")}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}

// ── RadioFilter ──────────────────────────────────────────────────────────────

interface RadioFilterProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}

export function RadioFilter({ label, value, onChange, options }: RadioFilterProps) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs font-medium text-slate-500">{label}</label>
      <div className="flex flex-wrap gap-1">
        {options.map((o) => (
          <button
            key={o.value}
            onClick={() => onChange(o.value)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
              value === o.value
                ? "bg-emerald-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── CheckboxFilter ───────────────────────────────────────────────────────────

interface CheckboxFilterProps {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}

export function CheckboxFilter({ label, checked, onChange }: CheckboxFilterProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer select-none">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
      />
      <span className="text-sm text-slate-600">{label}</span>
    </label>
  );
}

// ── MultiSelectFilter (react-select) ─────────────────────────────────────────

import ReactSelect from "react-select";

interface MultiSelectFilterProps {
  label: string;
  values: (string | number)[];
  onChange: (v: (string | number)[]) => void;
  options: (string | number)[];
}

export function MultiSelectFilter({
  label,
  values,
  onChange,
  options,
}: MultiSelectFilterProps) {
  const selectOptions = options.map((o) => ({ value: o, label: String(o) }));
  const selectValue   = values.map((v) => ({ value: v, label: String(v) }));

  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-slate-500">{label}</label>
      <ReactSelect
        isMulti
        instanceId={`filter-${label}`}
        options={selectOptions}
        value={selectValue}
        onChange={(selected) => onChange(selected.map((s) => s.value))}
        placeholder={`All ${label}s`}
        classNamePrefix="rs"
        styles={{
          control: (base, state) => ({
            ...base,
            minHeight: "34px",
            fontSize: "12px",
            borderColor: state.isFocused ? "#10b981" : "#e2e8f0",
            boxShadow: state.isFocused ? "0 0 0 2px #10b98133" : "none",
            "&:hover": { borderColor: "#10b981" },
          }),
          menu: (base) => ({ ...base, fontSize: "12px", zIndex: 50 }),
          multiValue: (base) => ({
            ...base,
            backgroundColor: "#d1fae5",
            borderRadius: "4px",
          }),
          multiValueLabel: (base) => ({ ...base, color: "#065f46", fontWeight: 500 }),
          multiValueRemove: (base) => ({
            ...base,
            color: "#065f46",
            "&:hover": { backgroundColor: "#6ee7b7", color: "#064e3b" },
          }),
          placeholder: (base) => ({ ...base, color: "#94a3b8", fontSize: "12px" }),
          valueContainer: (base) => ({ ...base, padding: "2px 8px" }),
        }}
      />
    </div>
  );
}

// ── FilterPanel (default) ─────────────────────────────────────────────────────

interface FilterPanelProps {
  children: React.ReactNode;
  onReset?: () => void;
  className?: string;
}

export default function FilterPanel({ children, onReset, className }: FilterPanelProps) {
  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white p-4 shadow-sm", className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <SlidersHorizontal size={15} />
          Filters
        </div>
        {onReset && (
          <button
            onClick={onReset}
            className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
          >
            Reset
          </button>
        )}
      </div>
      <div className="space-y-4">{children}</div>
    </div>
  );
}
