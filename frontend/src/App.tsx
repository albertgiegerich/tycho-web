import { useCallback, useEffect, useMemo, useState } from "react"
import { BitmapLayer } from '@deck.gl/layers';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { Layer, type DeckProps } from "deck.gl";
import Map, { useControl, type LngLat } from 'react-map-gl/maplibre';
import type { RasterResponse } from "./generated";

function DeckGLOverlay(props: DeckProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}


const App = () => {

  const [rasters, setRasters] = useState<RasterResponse[]>([]);
  const [selectedLatLng, setSelectedLatLng] = useState<LngLat | null>(null);
  const [selectedRaster, setSelectedRaster] = useState<RasterResponse | null>(null);

  useEffect(() => {


    const fetchFiles = async () => {
      const response = await fetch('http://localhost:8000/rasters')

      const rasters: RasterResponse[] = await response.json();

      setRasters(rasters);
    };

    fetchFiles()
  }, [])


  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (!file) {
      return
    };

    const formData = new FormData();
    formData.append('file', file);

    await fetch('http://localhost:8000/rasters', { method: 'POST', body: formData });
  }, []);


  const layers: Layer[] = useMemo(() => {

    if (selectedRaster) {
      return [new BitmapLayer({
        id: 'geotiff-bitmap',
        image: `http://localhost:8000/rasters/${selectedRaster.id}`,
        bounds: selectedRaster.bounds,
      })]
    }

    return [];
  }, [selectedRaster]);


  const onClickFile = useCallback(async (fileId: string) => {
    const file = rasters.find(f => f.id === fileId);

    if (file) {
      setSelectedRaster(file);
    }

  }, [rasters]);

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '240px',
        height: '100%',
        background: 'rgba(10, 10, 12, 0.75)',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px',
        boxSizing: 'border-box',
        zIndex: 1,
        backdropFilter: 'blur(4px)',
      }}>

        <input type="file" onChange={handleFileChange} style={{ marginTop: '12px', color: '#fff' }} />
        {selectedLatLng && (
          <div style={{ color: '#fff', fontSize: '12px', marginTop: '12px' }}>
            <div>Lat: {selectedLatLng.lat.toFixed(6)}</div>
            <div>Lng: {selectedLatLng.lng.toFixed(6)}</div>
          </div>
        )}
        {
          rasters.map(f => (
            <button
              onClick={() => onClickFile(f.id)}
              key={f.id}
              style={{
                padding: '8px 16px',
                background: '#e94560',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}>{f.name}</button>
          ))
        }
      </div>
      <Map
        initialViewState={{
          longitude: -122.4,
          latitude: 37.78,
          zoom: 10
        }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
        onClick={e => setSelectedLatLng(e.lngLat)}
      >
        <DeckGLOverlay layers={layers} />
      </Map>
    </div >
  )
}

export default App
