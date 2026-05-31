import { MapboxOverlay } from "@deck.gl/mapbox";
import { BitmapLayer, type DeckProps, type Layer } from "deck.gl";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useControl, useMap, type LngLat } from "react-map-gl/maplibre";
import { getPixel, listRasters, uploadRaster } from "../generated/sdk.gen";
import type { RasterOperation, RasterResponse } from "../generated";
import MapClickHandler from "./MapClickHandler";
import type { MapMouseEvent } from "maplibre-gl";
import Button from "@mui/material/Button";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select, { type SelectChangeEvent } from "@mui/material/Select";

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

  const [activeOperations, setActiveOperations] = useState<RasterOperation[]>(
    [],
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

  const onClickTrueColor = useCallback(() => {
    setActiveOperations((prevValue) => {
      if (prevValue.includes("true_color")) {
        return prevValue;
      }

      return [...prevValue, "true_color"];
    });
  }, []);

  const layers: Layer[] = useMemo(() => {
    if (selectedRaster) {
      const params = new URLSearchParams();

      for (const op of activeOperations) {
        params.append("operations", op);
      }

      return [
        new BitmapLayer({
          id: `geotiff-bitmap-${activeOperations.join("-")}`,
          image: `http://localhost:8000/rasters/${selectedRaster.id}?${params}`,
          bounds: selectedRaster.bounds,
          textureParameters: {
            minFilter: "linear", // Use bilinear interpolation to blend the pixels when zoomed out
            magFilter: "nearest", // When zoomed in show the individual pixels without interpolation
          },
        }),
      ];
    }

    return [];
  }, [activeOperations, selectedRaster]);

  const onClickMap = useCallback(
    (e: MapMouseEvent) => {
      setSelectedLngLat(e.lngLat);
      if (selectedRaster) {
        getPixel({
          query: { lat: e.lngLat.lat, lng: e.lngLat.lng },
          path: { id: selectedRaster?.id },
        });
      }
    },
    [selectedRaster],
  );

  const onSelectRaster = useCallback(
    (e: SelectChangeEvent) => {
      const raster = rasters.find((f) => f.id === e.target.value);
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
        <Button
          component="label"
          variant="contained"
          sx={{ marginTop: "12px" }}
        >
          Upload
          <input type="file" hidden onChange={handleFileChange} />
        </Button>
        {selectedLngLat && (
          <div style={{ color: "#fff", fontSize: "12px", marginTop: "12px" }}>
            <div>Lat: {selectedLngLat.lat.toFixed(6)}</div>
            <div>Lng: {selectedLngLat.lng.toFixed(6)}</div>
          </div>
        )}
        <FormControl fullWidth sx={{ marginTop: "12px" }}>
          <InputLabel sx={{ color: "#fff" }}>Raster</InputLabel>
          <Select
            value={selectedRaster?.id ?? ""}
            label="Raster"
            onChange={onSelectRaster}
            sx={{ color: "#fff" }}
          >
            {rasters.map((f) => (
              <MenuItem key={f.id} value={f.id}>
                {f.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          onClick={onClickTrueColor}
          variant="contained"
          color="primary"
          sx={{ marginTop: "12px" }}
        >
          True color
        </Button>
        <Button
          onClick={() => setActiveOperations([])}
          variant="contained"
          color="secondary"
          sx={{ marginTop: "12px" }}
          disabled={activeOperations.length === 0}
        >
          Reset
        </Button>
      </div>
      <DeckGLOverlay layers={layers} />
      <MapClickHandler onClick={onClickMap} />
    </>
  );
};

export default AppOverlay;
