import { Filter, MapPin, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  fetchActualWellStatuses,
  fetchProductionInjectionFormations,
  fetchWells,
  fetchWellStatuses,
  fetchWellTypes,
} from "../api/client.js";
import WellMap from "../components/WellMap.jsx";

export default function WellDashboard() {
  const [wells, setWells] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [actualStatuses, setActualStatuses] = useState([]);
  const [types, setTypes] = useState([]);
  const [formations, setFormations] = useState([]);
  const [filters, setFilters] = useState({
    search: "",
    status: "",
    actual_status: "",
    well_type: "",
    prod_inject_frmtn: [],
  });
  const [topN, setTopN] = useState(25);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [totalCount, setTotalCount] = useState(0);
  const [formationSearch, setFormationSearch] = useState("");

  useEffect(() => {
    Promise.all([fetchWellStatuses(), fetchWellTypes(), fetchProductionInjectionFormations()])
      .then(([statusOptions, typeOptions, formationOptions]) => {
        setStatuses(statusOptions);
        setTypes(typeOptions);
        const uniqueFormations = Array.from(
          new Map(formationOptions.map((formation) => [formation.value, formation])).values(),
        );
        setFormations(uniqueFormations);
      })
      .catch(() => setError("Unable to load filter options."));
  }, []);

  useEffect(() => {
    fetchActualWellStatuses(filters.status)
      .then((statusOptions) => setActualStatuses(statusOptions))
      .catch(() => setError("Unable to load detailed status options."));
  }, [filters.status]);

  useEffect(() => {
    setLoading(true);
    fetchWells(filters)
      .then((data) => {
        setWells(Array.isArray(data) ? data : data.results || []);
        setTotalCount(Array.isArray(data) ? data.length : data.count ?? data.results?.length ?? 0);
        setError("");
      })
      .catch(() => setError("Unable to load wells from the API."))
      .finally(() => setLoading(false));
  }, [filters]);

  const metrics = useMemo(() => {
    const mapped = wells.filter((well) => well.latitude && well.longitude).length;
    const active = wells.filter((well) => well.status === "Active").length;
    return { total: totalCount, mapped, active };
  }, [wells, totalCount]);

  const tableWells = useMemo(() => wells.slice(0, topN), [wells, topN]);
  const visibleFormations = useMemo(() => {
    const search = formationSearch.trim().toLowerCase();
    if (!search) return formations;
    return formations.filter((formation) => formation.label.toLowerCase().includes(search));
  }, [formations, formationSearch]);

  function updateFilter(key, value) {
    setFilters((current) => {
      if (key === "status") {
        return { ...current, status: value, actual_status: "" };
      }
      return { ...current, [key]: value };
    });
  }

  function toggleFormation(value) {
    setFilters((current) => {
      const selected = current.prod_inject_frmtn.includes(value)
        ? current.prod_inject_frmtn.filter((formation) => formation !== value)
        : [...current.prod_inject_frmtn, value];
      return { ...current, prod_inject_frmtn: selected };
    });
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Phase 1</p>
          <h1>Well Search</h1>
        </div>

        <label className="field">
          <span>Search UWI or name</span>
          <div className="input-with-icon">
            <Search size={16} />
            <input
              value={filters.search}
              onChange={(event) => updateFilter("search", event.target.value)}
              placeholder="100-06-10..."
            />
          </div>
        </label>

        <label className="field">
          <span>Well status</span>
          <select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
            <option value="">All statuses</option>
            {statuses.map((status) => (
              <option key={status.value} value={status.value}>{status.label}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Status detail</span>
          <select
            value={filters.actual_status}
            onChange={(event) => updateFilter("actual_status", event.target.value)}
          >
            <option value="">All details</option>
            {actualStatuses.map((status) => (
              <option key={status.value} value={status.value}>{status.label}</option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Well type</span>
          <select value={filters.well_type} onChange={(event) => updateFilter("well_type", event.target.value)}>
            <option value="">All types</option>
            {types.map((type) => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </label>

        <div className="field">
          <span>Production/injection formation</span>
          <div className="input-with-icon">
            <Search size={16} />
            <input
              value={formationSearch}
              onChange={(event) => setFormationSearch(event.target.value)}
              placeholder="Search formations..."
            />
          </div>
          <div className="formation-filter">
            <button
              type="button"
              className={`formation-chip ${filters.prod_inject_frmtn.length === 0 ? "selected" : ""}`}
              onClick={() => updateFilter("prod_inject_frmtn", [])}
            >
              All
            </button>
            {visibleFormations.map((formation) => (
              <button
                type="button"
                key={formation.value}
                className={`formation-chip ${filters.prod_inject_frmtn.includes(formation.value) ? "selected" : ""}`}
                onClick={() => toggleFormation(formation.value)}
                title={formation.label}
              >
                {formation.label}
              </button>
            ))}
            {visibleFormations.length === 0 && (
              <span className="formation-empty">No matching formations</span>
            )}
          </div>
        </div>

        <label className="field">
          <span>Table rows</span>
          <select value={topN} onChange={(event) => setTopN(Number(event.target.value))}>
            <option value={10}>Top 10</option>
            <option value={25}>Top 25</option>
            <option value={50}>Top 50</option>
            <option value={100}>Top 100</option>
          </select>
        </label>

        <div className="stat-grid">
          <div><strong>{metrics.total}</strong><span>Total</span></div>
          <div><strong>{metrics.active}</strong><span>Active</span></div>
          <div><strong>{metrics.mapped}</strong><span>Mapped</span></div>
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Django REST + PostGIS</p>
            <h2>Well Locations</h2>
          </div>
          <div className="status-pill">
            <Filter size={16} />
            {loading ? "Loading" : `${totalCount.toLocaleString()} wells`}
          </div>
        </header>

        {error && <div className="notice">{error}</div>}

        <div className="map-panel">
          <WellMap wells={wells} loading={loading} />
        </div>

        <section className="table-section">
          <div className="section-title">
            <MapPin size={18} />
            <h3>Well Register: Top {Math.min(topN, wells.length)}</h3>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>UWI</th>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Status Detail</th>
                  <th>Type</th>
                  <th>Operator</th>
                  <th>Location</th>
                </tr>
              </thead>
              <tbody>
                {tableWells.map((well) => (
                  <tr key={well.uwi}>
                    <td>{well.uwi}</td>
                    <td>{well.name}</td>
                    <td><span className={`tag ${well.status}`}>{well.status}</span></td>
                    <td>{well.actual_status_text || "-"}</td>
                    <td>{well.well_type}</td>
                    <td>{well.operator || "-"}</td>
                    <td>{well.latitude && well.longitude ? `${well.latitude}, ${well.longitude}` : "-"}</td>
                  </tr>
                ))}
                {!loading && tableWells.length === 0 && (
                  <tr>
                    <td colSpan="7" className="empty">No wells match the current filters.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}
