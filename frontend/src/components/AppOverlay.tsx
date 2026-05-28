import { MapboxOverlay } from "@deck.gl/mapbox";
import { BitmapLayer, type DeckProps, type Layer } from "deck.gl";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useControl, useMap, type LngLat } from "react-map-gl/maplibre";
import { listRasters, uploadRaster } from "../generated/sdk.gen";
import type { RasterResponse } from "../generated";
import MapClickHandler from "./MapClickHandler";
import type { MapMouseEvent } from "maplibre-gl";

function DeckGLOverlay(props: DeckProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

const AppOverlay = () => {
  const [rasters, setRasters] = useState<RasterResponse[]>([]);
  const [selectedLngLat, setSelectedLngLat] = useState<LngLat | null>(null);
  const [selectedRaster, setSelectedRaster] = useState<RasterResponse | null>(
    null,
  );

  const { current: map } = useMap();

  useEffect(() => {
    const fetchFiles = async () => {
      const { data } = await listRasters();
      if (data) {
        setRasters(data);
      }
    };

    fetchFiles();
  }, []);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];

      if (!file) {
        return;
      }

      const { data } = await uploadRaster({ body: { file } });

      console.log("uploaded", data);
      if (data) {
        setRasters((prevValue) => [...prevValue, data]);
      }
    },
    [],
  );

  const layers: Layer[] = useMemo(() => {
    if (selectedRaster) {
      return [
        new BitmapLayer({
          id: "geotiff-bitmap",
          image: `http://localhost:8000/rasters/${selectedRaster.id}`,
          bounds: selectedRaster.bounds,
        }),
      ];
    }

    return [];
  }, [selectedRaster]);

  const onClickMap = useCallback((e: MapMouseEvent) => {
    setSelectedLngLat(e.lngLat);
  }, []);

  const onClickFile = useCallback(
    async (fileId: string) => {
      const raster = rasters.find((f) => f.id === fileId);

      if (raster) {
        setSelectedRaster(raster);
        map?.fitBounds(raster.bounds, { padding: 40 });
      }
    },
    [map, rasters],
  );
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "240px",
          height: "100%",
          background: "rgba(10, 10, 12, 0.75)",
          display: "flex",
          flexDirection: "column",
          padding: "16px",
          boxSizing: "border-box",
          zIndex: 1,
          backdropFilter: "blur(4px)",
        }}
      >
        <input
          type="file"
          onChange={handleFileChange}
          style={{ marginTop: "12px", color: "#fff" }}
        />
        {selectedLngLat && (
          <div style={{ color: "#fff", fontSize: "12px", marginTop: "12px" }}>
            <div>Lat: {selectedLngLat.lat.toFixed(6)}</div>
            <div>Lng: {selectedLngLat.lng.toFixed(6)}</div>
          </div>
        )}
        {rasters.map((f) => (
          <button
            onClick={() => onClickFile(f.id)}
            key={f.id}
            style={{
              padding: "8px 16px",
              background: "#e94560",
              color: "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            {f.name}
          </button>
        ))}
      </div>
      <DeckGLOverlay layers={layers} />
      <MapClickHandler onClick={onClickMap} />
    </>
  );
};

export default AppOverlay;
