import maplibregl from "maplibre-gl";
import { useEffect } from "react";
import { useMap } from "react-map-gl/maplibre";

interface MapClickHandlerProps {
  onClick: (e: maplibregl.MapMouseEvent) => void;
}

const MapClickHandler = ({ onClick }: MapClickHandlerProps) => {
  const { current: map } = useMap();

  useEffect(() => {
    map?.on("click", onClick);
    return () => void map?.off("click", onClick);
  }, [map, onClick]);

  return null;
};

export default MapClickHandler;
