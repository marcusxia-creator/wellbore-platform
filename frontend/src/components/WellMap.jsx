import { GoogleMap, OverlayView, useJsApiLoader } from "@react-google-maps/api";
import { useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

const DEFAULT_CENTER = [54.5, -115.0];
const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
const GOOGLE_MAP_OPTIONS = {
  clickableIcons: false,
  fullscreenControl: false,
  mapTypeControl: false,
  streetViewControl: false,
};

function GoogleWellDot({ well }) {
  return (
    <OverlayView
      position={{ lat: Number(well.latitude), lng: Number(well.longitude) }}
      mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
    >
      <div className="google-dot" title={`${well.uwi} ${well.name}`}>
        <span className="google-dot-popup">
          <strong>{well.name}</strong>
          <small>{well.uwi}</small>
          <small>{well.status} / {well.well_type || "-"}</small>
        </span>
      </div>
    </OverlayView>
  );
}

function GoogleWellMap({ wells, mapType }) {
  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: GOOGLE_API_KEY || "",
  });

  const mappedWells = wells.filter((well) => well.latitude && well.longitude);
  const center = mappedWells.length
    ? { lat: Number(mappedWells[0].latitude), lng: Number(mappedWells[0].longitude) }
    : { lat: DEFAULT_CENTER[0], lng: DEFAULT_CENTER[1] };
  const options = useMemo(() => ({ ...GOOGLE_MAP_OPTIONS, mapTypeId: mapType }), [mapType]);

  if (!GOOGLE_API_KEY) {
    return (
      <div className="map-message">
        <strong>Google Maps API key required</strong>
        <span>Set VITE_GOOGLE_MAPS_API_KEY in the frontend environment to enable Google Map and Satellite modes.</span>
      </div>
    );
  }

  if (loadError) {
    return <div className="map-message">Unable to load Google Maps.</div>;
  }

  if (!isLoaded) {
    return (
      <div className="map-message">
        <span className="spinner" />
        <span>Loading Google Maps</span>
      </div>
    );
  }

  return (
    <GoogleMap
      center={center}
      zoom={mappedWells.length ? 7 : 5}
      mapContainerClassName="well-map"
      options={options}
    >
      {mappedWells.map((well) => (
        <GoogleWellDot key={well.uwi} well={well} />
      ))}
    </GoogleMap>
  );
}

export default function WellMap({ wells, loading }) {
  const [mapMode, setMapMode] = useState("leaflet");
  const mappedWells = wells.filter((well) => well.latitude && well.longitude);
  const center = mappedWells.length
    ? [Number(mappedWells[0].latitude), Number(mappedWells[0].longitude)]
    : DEFAULT_CENTER;

  return (
    <div className="map-wrap">
      <div className="map-mode-control" aria-label="Map mode">
        <button
          type="button"
          className={mapMode === "leaflet" ? "selected" : ""}
          onClick={() => setMapMode("leaflet")}
        >
          Road
        </button>
        <button
          type="button"
          className={mapMode === "google-roadmap" ? "selected" : ""}
          onClick={() => setMapMode("google-roadmap")}
        >
          Google Map
        </button>
        <button
          type="button"
          className={mapMode === "google-satellite" ? "selected" : ""}
          onClick={() => setMapMode("google-satellite")}
        >
          Satellite
        </button>
      </div>
      {loading && (
        <div className="map-loading" aria-live="polite">
          <span className="spinner" />
          <span>Loading wells</span>
        </div>
      )}
      {mapMode === "leaflet" && (
        <MapContainer center={center} zoom={mappedWells.length ? 7 : 5} scrollWheelZoom className="well-map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {mappedWells.map((well) => (
            <CircleMarker
              key={well.uwi}
              center={[Number(well.latitude), Number(well.longitude)]}
              radius={5}
              pathOptions={{
                color: "#083f49",
                fillColor: "#0fb783",
                fillOpacity: 0.95,
                opacity: 1,
                weight: 1.5,
              }}
            >
              <Popup>
                <strong>{well.name}</strong>
                <span>{well.uwi}</span>
                <span>{well.status} / {well.well_type}</span>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      )}
      {mapMode === "google-roadmap" && <GoogleWellMap wells={wells} mapType="roadmap" />}
      {mapMode === "google-satellite" && <GoogleWellMap wells={wells} mapType="satellite" />}
    </div>
  );
}
