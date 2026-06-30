import { useState, useEffect, useCallback, useMemo } from "react";
import type { Substation, SubstationFilters, MapMarker, FilterOption } from "@/lib/types";
import { fetchSubstations, fetchSubstationFilterOptions } from "@/lib/api";

export type ViewMode = "split" | "map" | "table";

export function useSubstations() {
  const [substations, setSubstations] = useState<Substation[]>([]);
  const [loading, setLoading]         = useState(true);
  const [total, setTotal]             = useState(0);
  const [viewMode, setViewMode]       = useState<ViewMode>("split");

  const [search, setSearch]           = useState("");
  const [area, setArea]               = useState("");
  const [areaOptions, setAreaOptions] = useState<FilterOption[]>([]);

  useEffect(() => {
    fetchSubstationFilterOptions()
      .then((opts) => setAreaOptions(opts.areas))
      .catch(() => setAreaOptions([
        { value: "AB", label: "AB" },
        { value: "SK", label: "SK" },
        { value: "BC", label: "BC" },
      ]));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const filters: SubstationFilters = {
        ...(search && { search }),
        ...(area   && { area }),
      };
      const res = await fetchSubstations(filters, 1, 1000);
      setSubstations(res.results);
      setTotal(res.count);
    } catch {
      setSubstations([]);
    } finally {
      setLoading(false);
    }
  }, [search, area]);

  useEffect(() => {
    const t = setTimeout(load, 400);
    return () => clearTimeout(t);
  }, [load]);

  const reset = () => { setSearch(""); setArea(""); };

  const markers = useMemo<MapMarker[]>(
    () => substations.map((s) => ({ type: "substation", data: s })),
    [substations]
  );

  const withCapacity = useMemo(
    () => substations.filter((s) => s.capacity_mw != null).length,
    [substations]
  );

  return {
    substations, loading, total, viewMode,
    search, area, areaOptions,
    setViewMode, setSearch, setArea, reset,
    markers, withCapacity,
  };
}
