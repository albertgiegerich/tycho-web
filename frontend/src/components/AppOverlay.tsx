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
import type {
  ContrastEnhancement,
  RasterOperation,
  RasterResponse,
} from "../generated";
import DensitySliceDialog from "./DensitySliceDialog";
import MapClickHandler from "./MapClickHandler";
import type { MapMouseEvent } from "maplibre-gl";
import Button from "@mui/material/Button";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormLabel from "@mui/material/FormLabel";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import Select, { type SelectChangeEvent } from "@mui/material/Select";
import styled from "@emotion/styled";
import { BandOrder } from "./BandOrder";

function DeckGLOverlay(props: DeckProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

const TRUE_COLOR_ID: ContrastEnhancement["id"] = "true_color";
const LINEAR_STRETCH_ID: ContrastEnhancement["id"] = "linear_stretch";

const CONTRAST_ENHANCEMENT_IDS = [TRUE_COLOR_ID, LINEAR_STRETCH_ID];

function isContrastEnhancementId(id: string): id is ContrastEnhancement["id"] {
  return (CONTRAST_ENHANCEMENT_IDS as readonly string[]).includes(id);
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
  const [contrastEnhancementId, setContrastEnhancementId] = useState<
    ContrastEnhancement["id"] | null
  >("linear_stretch");

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
          bandOrder,
          contrastEnhancement:
            contrastEnhancementId === null
              ? null
              : {
                  id: contrastEnhancementId,
                },
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
  }, [selectedRaster, activeOperations, bandOrder, contrastEnhancementId]);

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

  const onContrastEnhancementChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const id = e.target.value;

      if (isContrastEnhancementId(id)) {
        setContrastEnhancementId(id);
      } else {
        setContrastEnhancementId(null);
      }
    },
    [],
  );

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

        {selectedRaster && (
          <BandOrder
            bandCount={selectedRaster.bandCount}
            onChange={(bands) => setBandOrder(bands)}
          />
        )}
        <Button
          onClick={onDeleteRaster}
          variant="contained"
          color="error"
          disabled={selectedRaster === null}
        >
          Delete
        </Button>
        <FormControl disabled={selectedRaster === null}>
          <FormLabel sx={{ color: "#fff" }}>Contrast enhancement</FormLabel>
          <RadioGroup
            value={contrastEnhancementId}
            onChange={onContrastEnhancementChange}
          >
            <FormControlLabel
              value={LINEAR_STRETCH_ID}
              control={<Radio size="small" sx={{ color: "#fff" }} />}
              label="Linear stretch"
              sx={{ color: "#fff" }}
            />
            <FormControlLabel
              value={TRUE_COLOR_ID}
              control={<Radio size="small" sx={{ color: "#fff" }} />}
              label="True color"
              sx={{ color: "#fff" }}
            />
            <FormControlLabel
              value={null}
              control={<Radio size="small" sx={{ color: "#fff" }} />}
              label="None"
              sx={{ color: "#fff" }}
            />
          </RadioGroup>
        </FormControl>
        <Button
          onClick={() => setDensitySliceDialogOpen(true)}
          variant="contained"
          color="primary"
          disabled={selectedRaster === null}
        >
          Density Slice
        </Button>

        <Button
          onClick={() => {
            setActiveOperations([]);
            setContrastEnhancementId("linear_stretch");
            setBandOrder([1, 2, 3]);
          }}
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
