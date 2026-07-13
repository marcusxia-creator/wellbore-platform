"use client";

import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import type { Well, Substation, NearbyWellResult, BestPoint, WellSection } from "@/lib/types";

// ── Tile styles ───────────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const STYLES: Record<string, any> = {
  basic: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
  osm:   "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
  satellite: {
    version: 8,
    sources: {
      "esri-imagery": {
        type: "raster",
        tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
        tileSize: 256,
        attribution: "© Esri, Maxar, Earthstar Geographics",
      },
    },
    layers: [{ id: "background", type: "raster", source: "esri-imagery" }],
  },
};

// ── Types ─────────────────────────────────────────────────────────────────────

export type MapMarker =
  | { type: "well";       data: Well | NearbyWellResult }
  | { type: "substation"; data: Substation }
  | { type: "bestPoint";  data: BestPoint }
  | { type: "pin";        lat: number; lng: number; label?: string }
  | { type: "section";    data: WellSection };

interface WellMapProps {
  markers?: MapMarker[];
  center?: [number, number];
  zoom?: number;
  height?: string;
  onMapClick?: (lat: number, lng: number) => void;
  onSectionClick?: (strm: string) => void;
  selectedId?: number;
  tileStyle?: string;
  wellColorMode?: "status" | "volume";
  radiusCircle?: { lat: number; lng: number; radiusMiles: number };
}

// ── GeoJSON builders ──────────────────────────────────────────────────────────

type FC = { type: "FeatureCollection"; features: object[] };

function buildGeoJSON(markers: MapMarker[], wellColorMode: "status" | "volume") {
  const sections: object[] = [];
  const wells: object[] = [];
  const substations: object[] = [];
  const pins: object[] = [];

  let maxSecVol = 0;
  let maxWellVol = 0;
  for (const m of markers) {
    if (m.type === "section") maxSecVol = Math.max(maxSecVol, m.data.totalVolume);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (m.type === "well") maxWellVol = Math.max(maxWellVol, (m.data as any).available_volume_m3 ?? 0);
  }

  for (const m of markers) {
    if (m.type === "section") {
      const s = m.data as WellSection;
      if (!s.lat || !s.lng) continue;
      sections.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [s.lng, s.lat] },
        properties: {
          strm: s.strm, wellCount: s.wellCount, totalVolume: s.totalVolume,
          normVolume: maxSecVol > 0 ? s.totalVolume / maxSecVol : 0,
        },
      });
    } else if (m.type === "well") {
      const w = m.data as Well;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rec = w as any;
      const lat: number = rec.surf_latitude ?? rec.latitude;
      const lng: number = rec.surf_longitude ?? rec.longitude;
      if (!lat || !lng) continue;
      const vol: number = rec.available_volume_m3 ?? 0;
      wells.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [lng, lat] },
        properties: {
          id: w.id, uwi: rec.uwi ?? String(w.id),
          status: rec.well_status_group ?? "",
          volume: vol, normVolume: maxWellVol > 0 ? vol / maxWellVol : 0,
          colorMode: wellColorMode,
          distMi: "distance_miles" in w ? (w as NearbyWellResult).distance_miles.toFixed(1) : null,
        },
      });
    } else if (m.type === "substation") {
      const s = m.data as Substation;
      if (!s.latitude || !s.longitude) continue;
      substations.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [s.longitude, s.latitude] },
        properties: { name: s.name, code: s.facility_code, capacityMw: s.capacity_mw },
      });
    } else if (m.type === "pin") {
      if (!m.lat || !m.lng) continue;
      pins.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [m.lng, m.lat] },
        properties: { label: m.label ?? "" },
      });
    } else if (m.type === "bestPoint") {
      const bp = m.data as BestPoint;
      wells.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [bp.longitude, bp.latitude] },
        properties: { id: -1, uwi: "Best Point", status: "", volume: 0, normVolume: 0, colorMode: "status", distMi: null },
      });
    }
  }

  return {
    sections:    { type: "FeatureCollection", features: sections    } as FC,
    wells:       { type: "FeatureCollection", features: wells       } as FC,
    substations: { type: "FeatureCollection", features: substations } as FC,
    pins:        { type: "FeatureCollection", features: pins        } as FC,
  };
}

// Approximate a radius (in miles) around a point as a 64-vertex GeoJSON polygon.
function buildCircleGeoJSON(c?: { lat: number; lng: number; radiusMiles: number }): FC {
  if (!c) return { type: "FeatureCollection", features: [] };
  const degPerMile = 1 / 69.0; // ~69 miles per degree of latitude
  const coords: [number, number][] = [];
  for (let i = 0; i <= 64; i++) {
    const theta = (i / 64) * 2 * Math.PI;
    const dLat = c.radiusMiles * degPerMile * Math.sin(theta);
    const dLng = (c.radiusMiles * degPerMile * Math.cos(theta)) / Math.cos((c.lat * Math.PI) / 180);
    coords.push([c.lng + dLng, c.lat + dLat]);
  }
  return {
    type: "FeatureCollection",
    features: [{ type: "Feature", geometry: { type: "Polygon", coordinates: [coords] }, properties: {} }],
  };
}

// ── Layer setup ───────────────────────────────────────────────────────────────

// Volume ramp: green → yellow → red  (matches Dash color_continuous_scale)
const VOL_COLOR = [
  "interpolate", ["linear"], ["get", "normVolume"],
  0, "#00b050", 0.5, "#ffff00", 1, "#ff0000",
];
const VOL_STROKE = [
  "interpolate", ["linear"], ["get", "normVolume"],
  0, "#005a2b", 0.5, "#b8a800", 1, "#9a0000",
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function addSourcesAndLayers(map: any) {
  const empty: FC = { type: "FeatureCollection", features: [] };
  for (const id of ["radius", "sections", "wells", "substations", "pins"])
    if (!map.getSource(id)) map.addSource(id, { type: "geojson", data: empty });

  // Radius circle first so it renders beneath the markers.
  if (!map.getLayer("radius-fill"))
    map.addLayer({ id: "radius-fill", type: "fill", source: "radius", paint: {
      "fill-color": "#10b981",
      "fill-opacity": 0.08,
    }});
  if (!map.getLayer("radius-line"))
    map.addLayer({ id: "radius-line", type: "line", source: "radius", paint: {
      "line-color": "#059669",
      "line-width": 2,
      "line-dasharray": [2, 2],
    }});

  if (!map.getLayer("sections-layer"))
    map.addLayer({ id: "sections-layer", type: "circle", source: "sections", paint: {
      "circle-radius":       ["interpolate", ["linear"], ["get", "normVolume"], 0, 6, 1, 26],
      "circle-color":        VOL_COLOR,
      "circle-opacity":      0.85,
      "circle-stroke-width": 1.5,
      "circle-stroke-color": VOL_STROKE,
    }});

  // Wells colored by status (drill-down view)
  if (!map.getLayer("wells-status"))
    map.addLayer({ id: "wells-status", type: "circle", source: "wells",
      filter: ["==", ["get", "colorMode"], "status"],
      paint: {
        "circle-radius": 5,
        "circle-color": ["match", ["get", "status"], "IDLE", "#10b981", "SUSP", "#f59e0b", "ABD", "#ef4444", "#64748b"],
        "circle-opacity": 0.9,
        "circle-stroke-width": 1,
        "circle-stroke-color": "white",
      }});

  // Wells sized + colored by volume (NTS view)
  if (!map.getLayer("wells-volume"))
    map.addLayer({ id: "wells-volume", type: "circle", source: "wells",
      filter: ["==", ["get", "colorMode"], "volume"],
      paint: {
        "circle-radius":       ["interpolate", ["linear"], ["get", "normVolume"], 0, 4, 1, 20],
        "circle-color":        VOL_COLOR,
        "circle-opacity":      0.85,
        "circle-stroke-width": 1,
        "circle-stroke-color": VOL_STROKE,
      }});

  if (!map.getLayer("substations-fill"))
    map.addLayer({ id: "substations-fill", type: "circle", source: "substations",
      paint: {
        "circle-radius": 5,
        "circle-color": "#eab308",
        "circle-opacity": 0.9,
        "circle-stroke-width": 1,
        "circle-stroke-color": "white",
      } });

  // Search-center pin on top of everything else
  if (!map.getLayer("pins-layer"))
    map.addLayer({ id: "pins-layer", type: "circle", source: "pins", paint: {
      "circle-radius": 7,
      "circle-color": "#2563eb",
      "circle-opacity": 1,
      "circle-stroke-width": 2,
      "circle-stroke-color": "white",
    }});
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function setData(map: any, geojson: ReturnType<typeof buildGeoJSON>) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (map.getSource("sections")    as any)?.setData(geojson.sections);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (map.getSource("wells")       as any)?.setData(geojson.wells);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (map.getSource("substations") as any)?.setData(geojson.substations);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (map.getSource("pins")        as any)?.setData(geojson.pins);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function setRadius(map: any, c?: { lat: number; lng: number; radiusMiles: number }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (map.getSource("radius") as any)?.setData(buildCircleGeoJSON(c));
}

// ── Popup helpers ─────────────────────────────────────────────────────────────

type Props = Record<string, unknown>;
const fmt = (n: unknown) => Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });

const popupHtml = (layerId: string, p: Props) =>
  layerId === "sections-layer"
    ? `<b>Section ${p.strm}</b><br/>Wells: ${p.wellCount}<br/>Volume: ${fmt(p.totalVolume)} m³`
  : layerId === "wells-status" || layerId === "wells-volume"
    ? `<b>${p.uwi}</b><br/>Status: ${p.status}<br/>Volume: ${fmt(p.volume)} m³${p.distMi ? `<br/>Distance: ${p.distMi} mi` : ""}`
  : `<b>${p.name}</b>`;

// ── Component ─────────────────────────────────────────────────────────────────

export default function WellMap({
  markers       = [],
  center        = [53.5, -115.0],
  zoom          = 6,
  height        = "100%",
  onMapClick,
  onSectionClick,
  tileStyle     = "basic",
  wellColorMode = "status",
  radiusCircle,
}: WellMapProps) {
  const containerRef   = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef         = useRef<any>(null);
  const markersRef     = useRef(markers);
  const colorModeRef   = useRef(wellColorMode);
  const onSectionRef   = useRef(onSectionClick);
  const onMapClickRef  = useRef(onMapClick);
  const radiusRef      = useRef(radiusCircle);

  useEffect(() => { markersRef.current   = markers;       }, [markers]);
  useEffect(() => { colorModeRef.current = wellColorMode; }, [wellColorMode]);
  useEffect(() => { radiusRef.current    = radiusCircle;  }, [radiusCircle]);
  useEffect(() => { onSectionRef.current = onSectionClick;}, [onSectionClick]);
  useEffect(() => { onMapClickRef.current = onMapClick;   }, [onMapClick]);

  // Init map once
  useEffect(() => {
    if (!containerRef.current) return;
    let alive = true;

    import("maplibre-gl").then(({ default: maplibregl }) => {
      if (!alive || !containerRef.current) return;

      const map = new maplibregl.Map({
        container: containerRef.current,
        style:     STYLES[tileStyle] ?? STYLES.basic,
        center:    [center[1], center[0]],
        zoom,
        attributionControl: false,
      });
      map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");

      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, maxWidth: "260px" });

      // Re-add sources/layers after every style load (init + setStyle).
      // Also call resize() here: the container may not have its final CSS dimensions
      // when the map is first constructed (common in flex layouts), which leaves the
      // canvas blank. resize() forces MapLibre to re-read the container size.
      map.on("style.load", () => {
        if (!alive) return;
        map.resize();
        addSourcesAndLayers(map);
        setData(map, buildGeoJSON(markersRef.current, colorModeRef.current));
        setRadius(map, radiusRef.current);
      });

      // Keep the canvas in sync if the container is resized later
      // (e.g. sidebar collapse, window resize).
      const ro = new ResizeObserver(() => { map.resize(); });
      if (containerRef.current) ro.observe(containerRef.current);

      const HOVER = ["sections-layer", "wells-status", "wells-volume", "substations-fill"];

      map.on("mousemove", (e: { point: unknown; lngLat: { lat: number; lng: number } }) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const features = map.queryRenderedFeatures(e.point as any, { layers: HOVER });
        if (!features.length) { map.getCanvas().style.cursor = ""; popup.remove(); return; }
        const f   = features[0];
        const lid = f.layer.id as string;
        map.getCanvas().style.cursor = lid === "sections-layer" ? "pointer" : "default";
        popup.setLngLat([e.lngLat.lng, e.lngLat.lat])
          .setHTML(popupHtml(lid, f.properties as Props))
          .addTo(map);
      });

      map.on("mouseleave", () => { map.getCanvas().style.cursor = ""; popup.remove(); });

      map.on("click", (e: { point: unknown; lngLat: { lat: number; lng: number } }) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const sec = map.queryRenderedFeatures(e.point as any, { layers: ["sections-layer"] });
        if (sec.length) onSectionRef.current?.((sec[0].properties as Props).strm as string);
        else            onMapClickRef.current?.(e.lngLat.lat, e.lngLat.lng);
      });

      mapRef.current = map;
      mapRef.current._ro = ro; // stash so cleanup can disconnect it
    });

    return () => {
      alive = false;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (mapRef.current as any)?._ro?.disconnect();
      mapRef.current?.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update GeoJSON data when markers or colorMode change.
  // If the style isn't ready yet, the style.load handler will pick up the latest
  // markersRef when it fires — so we only need to act when the style is already up.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (map.isStyleLoaded()) {
      setData(map, buildGeoJSON(markers, wellColorMode));
    } else {
      // Style is mid-load (e.g. tile-style switch just triggered); let style.load handle it.
      // markersRef is already up-to-date so no data will be missed.
      const onLoad = () => {
        map.resize();
        addSourcesAndLayers(map);
        setData(map, buildGeoJSON(markersRef.current, colorModeRef.current));
        setRadius(map, radiusRef.current);
      };
      map.once("style.load", onLoad);
      return () => { map.off("style.load", onLoad); };
    }
  }, [markers, wellColorMode]);

  // Update the search-radius circle when it changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return; // style.load handler covers the pending case
    setRadius(map, radiusCircle);
  }, [radiusCircle]);

  // Swap tile style
  useEffect(() => {
    mapRef.current?.setStyle(STYLES[tileStyle] ?? STYLES.basic);
  }, [tileStyle]);

  // Fly to new center/zoom on drill-down
  useEffect(() => {
    mapRef.current?.flyTo({ center: [center[1], center[0]], zoom, duration: 900 });
  }, [center, zoom]);

  return <div ref={containerRef} style={{ height, width: "100%", borderRadius: "0.75rem", overflow: "hidden" }} />;
}
