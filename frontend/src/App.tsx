import { useCallback, useEffect, useState } from "react"
import { ScatterplotLayer } from '@deck.gl/layers';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { type DeckProps } from "deck.gl";
import Map, { useControl } from 'react-map-gl/maplibre';
import type { FileRecordResponse } from "./generated";

function DeckGLOverlay(props: DeckProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

const App = () => {

  const [files, setFiles] = useState<FileRecordResponse[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);

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

  const scatterplotLayer = new ScatterplotLayer({
    id: 'bart-stations',
    data: 'https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/bart-stations.json',
    getRadius: d => Math.sqrt(d.entries),
    radiusScale: 6,
    radiusMinPixels: 4,
    getPosition: d => d.coordinates,
    getColor: [255, 0, 0],
  });

  const onClickFile = useCallback(async (fileId: string) => {
    setSelectedFileId(fileId);

    const response = await fetch(`http://localhost:8000/files/${fileId}`)
  }, []);


  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '240px',
        height: '100%',
        background: 'rgba(26, 26, 46, 0.75)',
        display: 'flex',
        flexDirection: 'column',
        padding: '16px',
        boxSizing: 'border-box',
        zIndex: 1,
        backdropFilter: 'blur(4px)',
      }}>

        <input type="file" onChange={handleFileChange} style={{ marginTop: '12px', color: '#fff' }} />
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
      >
        <DeckGLOverlay layers={[scatterplotLayer]} />
      </Map>
    </div >
  )
}

export default App
