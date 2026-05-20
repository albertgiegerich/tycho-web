import { useCallback, useEffect } from "react"
import { ScatterplotLayer } from '@deck.gl/layers';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { type DeckProps } from "deck.gl";
import Map, { useControl } from 'react-map-gl/maplibre';

function DeckGLOverlay(props: DeckProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay(props));
  overlay.setProps(props);
  return null;
}

const App = () => {
  useEffect(() => {
    (async () => {
      const response = await fetch('http://localhost:8000')
      console.log(await response.json());
    })();
  }, [])


  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (!file) {
      return
    };

    const formData = new FormData();
    formData.append('file', file);

    await fetch('http://localhost:8000/uploadfile', { method: 'POST', body: formData });
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
        <button style={{
          padding: '8px 16px',
          background: '#e94560',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
        }}>
          Button
        </button>
        <input type="file" onChange={handleFileChange} style={{ marginTop: '12px', color: '#fff' }} />
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
    </div>
  )
}

export default App
