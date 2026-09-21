import { useEffect, useRef } from "react";
import L from "leaflet";
import { useMap } from "react-leaflet";
import "@geoman-io/leaflet-geoman-free";
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";
import { MAP_CONFIG } from "@/lib/mapConfig";

const PATH_OPTIONS = { color: "#00a86b", fillColor: "#00c781", fillOpacity: 0.22, weight: 4 };

function geometryFromLayer(layer) {
  const feature = layer.toGeoJSON();
  return feature?.geometry?.type === "Polygon" ? feature.geometry : null;
}

function addLayer(map, geometry, ref, onGeometryChange) {
  if (!geometry || geometry.type !== "Polygon") return;
  const layerGroup = L.geoJSON({ type: "Feature", properties: {}, geometry }, { style: PATH_OPTIONS });
  layerGroup.eachLayer((layer) => {
    ref.current = layer;
    layer.addTo(map);
    const update = () => {
      const next = geometryFromLayer(layer);
      if (next) onGeometryChange(next);
    };
    layer.on("pm:edit", update);
    layer.on("pm:update", update);
    layer.on("pm:remove", () => { ref.current = null; onGeometryChange(null); });
  });
}

export default function BoundaryDrawingController({ geometry, command, onGeometryChange, onDrawingChange, onError }) {
  const map = useMap();
  const polygonLayerRef = useRef(null);
  const pendingZoomHandlerRef = useRef(null);

  useEffect(() => {
    map.pm.setGlobalOptions({
      snappable: false,
      allowSelfIntersection: false,
      continueDrawing: false,
      markerEditable: true,
      hideMiddleMarkers: false,
      pathOptions: PATH_OPTIONS,
      templineStyle: { color: "#00a86b", weight: 3 },
      hintlineStyle: { color: "#ffffff", dashArray: [6, 6], weight: 2 },
    });

    const updateLayer = (layer) => {
      const next = geometryFromLayer(layer);
      if (next) onGeometryChange(next);
    };
    const handleCreate = (event) => {
      if (event.shape !== "Polygon") { map.removeLayer(event.layer); return; }
      if (polygonLayerRef.current) map.removeLayer(polygonLayerRef.current);
      polygonLayerRef.current = event.layer;
      event.layer.on("pm:edit pm:update", () => updateLayer(event.layer));
      event.layer.on("pm:remove", () => { polygonLayerRef.current = null; onGeometryChange(null); });
      updateLayer(event.layer);
      onDrawingChange(false);
    };
    const handleDrawStart = () => onDrawingChange(true);
    const handleDrawEnd = () => onDrawingChange(false);
    const handleIntersection = () => onError("Boundary lines cannot cross each other. Move the last point.");

    map.on("pm:create", handleCreate);
    map.on("pm:drawstart", handleDrawStart);
    map.on("pm:drawend", handleDrawEnd);
    map.on("pm:intersect", handleIntersection);
    return () => {
      map.pm.disableDraw();
      map.pm.disableGlobalEditMode();
      if (pendingZoomHandlerRef.current) {
        map.off("zoomend", pendingZoomHandlerRef.current);
        pendingZoomHandlerRef.current = null;
      }
      map.off("pm:create", handleCreate);
      map.off("pm:drawstart", handleDrawStart);
      map.off("pm:drawend", handleDrawEnd);
      map.off("pm:intersect", handleIntersection);
      if (polygonLayerRef.current) map.removeLayer(polygonLayerRef.current);
    };
  }, [map, onDrawingChange, onError, onGeometryChange]);

  useEffect(() => {
    if (!command) return;

    if (pendingZoomHandlerRef.current) {
      map.off("zoomend", pendingZoomHandlerRef.current);
      pendingZoomHandlerRef.current = null;
    }

    const enablePolygonDrawing = () => {
      pendingZoomHandlerRef.current = null;
      if (polygonLayerRef.current) {
        map.removeLayer(polygonLayerRef.current);
        polygonLayerRef.current = null;
        onGeometryChange(null);
      }
      map.pm.disableGlobalEditMode();
      map.pm.enableDraw("Polygon", {
        allowSelfIntersection: false,
        continueDrawing: false,
        snappable: false,
        markerEditable: true,
        finishOn: null,
      });
      onDrawingChange(true);
      onError("");
    };

    if (command.type === "start-drawing") {
      const minimumZoom = MAP_CONFIG.zoom.minimumDrawing;
      if (map.getZoom() < minimumZoom) {
        onError(`Zooming in to level ${minimumZoom}. Tap each farm corner when drawing mode is ready.`);
        pendingZoomHandlerRef.current = enablePolygonDrawing;
        map.once("zoomend", enablePolygonDrawing);
        map.setZoom(minimumZoom, { animate: true });
      } else {
        enablePolygonDrawing();
      }
    } else if (command.type === "edit") {
      map.pm.disableDraw();
      map.pm.enableGlobalEditMode({ allowSelfIntersection: false });
      onDrawingChange(false);
    } else if (command.type === "stop-editing") {
      map.pm.disableGlobalEditMode();
      onDrawingChange(false);
    } else if (command.type === "clear") {
      map.pm.disableDraw(); map.pm.disableGlobalEditMode();
      if (polygonLayerRef.current) { map.removeLayer(polygonLayerRef.current); polygonLayerRef.current = null; }
      onGeometryChange(null);
      onDrawingChange(false);
    } else if (command.type === "replace") {
      map.pm.disableDraw(); map.pm.disableGlobalEditMode();
      if (polygonLayerRef.current) { map.removeLayer(polygonLayerRef.current); polygonLayerRef.current = null; }
      addLayer(map, command.geometry, polygonLayerRef, onGeometryChange);
      onDrawingChange(false);
    }
  }, [command, map, onError, onGeometryChange]);

  useEffect(() => {
    if (polygonLayerRef.current || !geometry || geometry.type !== "Polygon") return;
    addLayer(map, geometry, polygonLayerRef, onGeometryChange);
  }, [geometry, map, onGeometryChange]);

  return null;
}
