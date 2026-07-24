"use client";

import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import type { Well } from "@/lib/types";

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

export type MapMarker = { type: "well"; data: Well };

interface WellMapProps {
  markers?: MapMarker[];
  center?: [number, number];
  zoom?: number;
  height?: string;
  tileStyle?: string;
}

// ── GeoJSON builder ─────────────────────────────────────────────────────────

type FC = { type: "FeatureCollection"; features: object[] };

function buildGeoJSON(markers: MapMarker[]): FC {
  const wells: object[] = [];
  for (const m of markers) {
    if (m.type !== "well") continue;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const rec = m.data as any;
    const lat: number = rec.surf_latitude ?? rec.latitude;
    const lng: number = rec.surf_longitude ?? rec.longitude;
    if (!lat || !lng) continue;
    wells.push({
      type: "Feature",
      geometry: { type: "Point", coordinates: [lng, lat] },
      properties: {
        id: rec.id,
        uwi: rec.uwi ?? String(rec.id),
        name: rec.name ?? "",
        status: rec.well_status_group ?? "",
      },
    });
  }
  return { type: "FeatureCollection", features: wells };
}

// ── Layer setup ───────────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function addSourcesAndLayers(map: any) {
  const empty: FC = { type: "FeatureCollection", features: [] };
  if (!map.getSource("wells")) map.addSource("wells", { type: "geojson", data: empty });

  if (!map.getLayer("wells-status"))
    map.addLayer({
      id: "wells-status",
      type: "circle",
      source: "wells",
      paint: {
        "circle-radius": 5,
        "circle-color": ["match", ["get", "status"],
          ["IDLE", "Active"], "#10b981",
          ["SUSP", "Suspended"], "#f59e0b",
          "ABD", "#ef4444",
          "Inactive", "#64748b",
          "#94a3b8"],
        "circle-opacity": 0.9,
        "circle-stroke-width": 1,
        "circle-stroke-color": "white",
      },
    });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function setData(map: any, geojson: FC) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (map.getSource("wells") as any)?.setData(geojson);
}

// ── Popup helper ──────────────────────────────────────────────────────────────

type Props = Record<string, unknown>;

const popupHtml = (p: Props) =>
  `<b>${p.uwi}</b>${p.name ? `<br/>${p.name}` : ""}<br/>Status: ${p.status}`;

// ── Component ─────────────────────────────────────────────────────────────────

export default function WellMap({
  markers   = [],
  center    = [53.5, -115.0],
  zoom      = 6,
  height    = "100%",
  tileStyle = "basic",
}: WellMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef       = useRef<any>(null);
  const markersRef   = useRef(markers);

  useEffect(() => { markersRef.current = markers; }, [markers]);

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

      // Re-add sources/layers after every style load (init + setStyle). resize()
      // here forces MapLibre to re-read the container size in flex layouts.
      map.on("style.load", () => {
        if (!alive) return;
        map.resize();
        addSourcesAndLayers(map);
        setData(map, buildGeoJSON(markersRef.current));
      });

      const ro = new ResizeObserver(() => { map.resize(); });
      if (containerRef.current) ro.observe(containerRef.current);

      map.on("mousemove", "wells-status", (e: { features?: { properties: Props }[]; lngLat: { lat: number; lng: number } }) => {
        map.getCanvas().style.cursor = "default";
        const f = e.features?.[0];
        if (!f) return;
        popup.setLngLat([e.lngLat.lng, e.lngLat.lat]).setHTML(popupHtml(f.properties)).addTo(map);
      });
      map.on("mouseleave", "wells-status", () => { map.getCanvas().style.cursor = ""; popup.remove(); });

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

  // Update GeoJSON when markers change.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (map.isStyleLoaded()) {
      setData(map, buildGeoJSON(markers));
    } else {
      const onLoad = () => {
        map.resize();
        addSourcesAndLayers(map);
        setData(map, buildGeoJSON(markersRef.current));
      };
      map.once("style.load", onLoad);
      return () => { map.off("style.load", onLoad); };
    }
  }, [markers]);

  // Swap tile style
  useEffect(() => {
    mapRef.current?.setStyle(STYLES[tileStyle] ?? STYLES.basic);
  }, [tileStyle]);

  // Fly to new center/zoom
  useEffect(() => {
    mapRef.current?.flyTo({ center: [center[1], center[0]], zoom, duration: 900 });
  }, [center, zoom]);

  return <div ref={containerRef} style={{ height, width: "100%", borderRadius: "0.75rem", overflow: "hidden" }} />;
}
