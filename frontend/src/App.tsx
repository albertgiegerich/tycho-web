import Map from "react-map-gl/maplibre";
import AppOverlay from "./components/AppOverlay";

const App = () => {
  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh" }}>
      <Map
        initialViewState={{
          longitude: -122.4,
          latitude: 37.78,
          zoom: 10,
        }}
        mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
      >
        <AppOverlay />
      </Map>
    </div>
  );
};

export default App;
