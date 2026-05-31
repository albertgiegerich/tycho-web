import { MapboxOverlay } from "@deck.gl/mapbox";
import { BitmapLayer, type DeckProps, type Layer } from "deck.gl";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useControl, useMap, type LngLat } from "react-map-gl/maplibre";
import {
  deleteRaster,
  getPixel,
  getRaster,
  listRasters,
  uploadRaster,
} from "../generated/sdk.gen";
import type { RasterOperation, RasterResponse } from "../generated";
import DensitySliceDialog from "./DensitySliceDialog";
import MapClickHandler from "./MapClickHandler";
import type { MapMouseEvent } from "maplibre-gl";
import Button from "@mui/material/Button";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select, { type SelectChangeEvent } from "@mui/material/Select";
import styled from "@emotion/styled";
import { BandOrder } from "./BandOrder";

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
  const [rasterImageUrl, setRasterImageUrl] = useState<string | null>(null);

  const [activeOperations, setActiveOperations] = useState<RasterOperation[]>(
    [],
  );
  const [densitySliceDialogOpen, setDensitySliceDialogOpen] = useState(false);
  const [bandOrder, setBandOrder] = useState<[number, number, number]>([
    1, 2, 3,
  ]);

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

  useEffect(() => {
    if (!selectedRaster) {
      return;
    }

    const updateRasterImageUrl = async () => {
      const { data } = await getRaster({
        path: { id: selectedRaster.id },
        body: {
          band_order: bandOrder,
          operations: activeOperations,
        },
      });

      if (!data) {
        return;
      }

      const url = URL.createObjectURL(data as Blob);
      setRasterImageUrl((prev) => {
        if (prev) {
          URL.revokeObjectURL(prev);
        }

        return url;
      });
    };

    updateRasterImageUrl();
  }, [selectedRaster, activeOperations, bandOrder]);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];

      if (!file) {
        return;
      }

      const { data } = await uploadRaster({ body: { file } });

      if (data) {
        setRasters((prevValue) => [...prevValue, data]);
      }
    },
    [],
  );

  const onClickTrueColor = useCallback(() => {
    setActiveOperations((prevValue) => {
      if (prevValue.some((op) => op.id === "true_color")) {
        return prevValue;
      }

      return [...prevValue, { id: "true_color" }];
    });
  }, []);

  const layers: Layer[] = useMemo(() => {
    if (selectedRaster && rasterImageUrl) {
      return [
        new BitmapLayer({
          id: `geotiff-bitmap`,
          image: rasterImageUrl,
          bounds: selectedRaster.bounds,
          textureParameters: {
            minFilter: "linear", // Use bilinear interpolation to blend the pixels when zoomed out
            magFilter: "nearest", // When zoomed in show the individual pixels without interpolation
          },
        }),
      ];
    }

    return [];
  }, [rasterImageUrl, selectedRaster]);

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

  const onDeleteRaster = useCallback(async () => {
    if (!selectedRaster) {
      return;
    }

    await deleteRaster({ path: { id: selectedRaster.id } });

    setRasters((prev) => prev.filter((r) => r.id !== selectedRaster.id));

    setSelectedRaster(null);

    setRasterImageUrl((prev) => {
      if (prev) {
        URL.revokeObjectURL(prev);
      }

      return null;
    });
  }, [selectedRaster]);

  return (
    <>
      <SideBar>
        <Button component="label" variant="contained">
          Upload
          <input type="file" hidden onChange={handleFileChange} />
        </Button>
        {selectedLngLat && (
          <div style={{ color: "#fff", fontSize: "12px" }}>
            <div>Lat: {selectedLngLat.lat.toFixed(6)}</div>
            <div>Lng: {selectedLngLat.lng.toFixed(6)}</div>
          </div>
        )}
        <FormControl fullWidth>
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
        <BandOrder onChange={(bands) => setBandOrder(bands)} />
        <Button
          onClick={onDeleteRaster}
          variant="contained"
          color="error"
          disabled={selectedRaster === null}
        >
          Delete
        </Button>
        <Button
          onClick={onClickTrueColor}
          variant="contained"
          color="primary"
          disabled={
            selectedRaster === null ||
            activeOperations.some((op) => op.id === "true_color")
          }
        >
          True color
        </Button>
        <Button
          onClick={() => setDensitySliceDialogOpen(true)}
          variant="contained"
          color="primary"
          disabled={selectedRaster === null}
        >
          Density Slice
        </Button>

        <Button
          onClick={() => setActiveOperations([])}
          variant="contained"
          color="secondary"
          disabled={activeOperations.length === 0}
        >
          Reset
        </Button>
      </SideBar>
      <DensitySliceDialog
        open={densitySliceDialogOpen}
        onClose={() => setDensitySliceDialogOpen(false)}
        onApply={(breaks) =>
          setActiveOperations((prev) => [
            ...prev,
            { id: "density_slice", breaks },
          ])
        }
      />
      <DeckGLOverlay layers={layers} />
      <MapClickHandler onClick={onClickMap} />
    </>
  );
};

const SideBar = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 240px;
  height: 100%;
  background: rgba(10, 10, 12, 0.75);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  box-sizing: border-box;
  z-index: 1;
  backdrop-filter: blur(4px);
`;

export default AppOverlay;
