import { useEffect } from "react"
import { ScatterplotLayer } from '@deck.gl/layers';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { type DeckProps } from "deck.gl";
import Map, { useControl } from 'react-map-gl/maplibre';

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

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
    <div style={{ width: '100vw', height: '100vh' }}>
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
