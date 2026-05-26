import { useCallback, useEffect, useMemo, useState } from "react"
import { BitmapLayer } from '@deck.gl/layers';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { Layer, type DeckProps } from "deck.gl";
import Map, { useControl, type LngLat } from 'react-map-gl/maplibre';
import type { FileRecordResponse } from "./generated";

function DeckGLOverlay(props: DeckProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}


const App = () => {

  const [files, setFiles] = useState<FileRecordResponse[]>([]);
  const [selectedLatLng, setSelectedLatLng] = useState<LngLat | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileRecordResponse | null>(null);

  useEffect(() => {


    const fetchFiles = async () => {
      const response = await fetch('http://localhost:8000/files')

      const fileRecords: FileRecordResponse[] = await response.json();

      setFiles(fileRecords);
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

    await fetch('http://localhost:8000/files', { method: 'POST', body: formData });
  }, []);


  const layers: Layer[] = useMemo(() => {

    if (selectedFile) {
      return [new BitmapLayer({
        id: 'geotiff-bitmap',
        image: `http://localhost:8000/files/${selectedFile.id}`,
        bounds: selectedFile.bounds,
      })]
    }

    return [];
  }, [selectedFile]);


  const onClickFile = useCallback(async (fileId: string) => {
    const file = files.find(f => f.id === fileId);

    if (file) {
      setSelectedFile(file);
    }

  }, [files]);

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
          files.map(f => (
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
