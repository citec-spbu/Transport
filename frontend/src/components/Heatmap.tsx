import { useEffect, useRef } from "react";
import L from "leaflet";
import Card from "./ui/Card";

type ApiMetricNode = {
  id: string;
  name: string;
  metric: number;
  coordinates: [number, number]; // [longitude, latitude]
};

export default function Heatmap({
  nodes: apiNodes,
  metricType,
  title,
}: {
  nodes: ApiMetricNode[];
  metricType: "pagerank" | "betweenness";
  title: string;
}) {
  const initializedViewRef = useRef(false);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const initialBoundsRef = useRef<L.LatLngBounds | null>(null);

  useEffect(() => {
    if (mapRef.current || !containerRef.current) return;

    const map = L.map(containerRef.current, {
      zoomControl: false,
      zoom: 10,
    });

    // Кнопка зума
    L.control.zoom({ position: "topleft" }).addTo(map);

    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
      {
        maxZoom: 18,
        opacity: 0.65,
        attribution: "© OpenStreetMap contributors",
      }
    ).addTo(map);

    mapRef.current = map;

// Кнопка центрирования карты
    const ResetControl = L.Control.extend({
      onAdd: function(map: L.Map)  {
        const container = L.DomUtil.create("div", "leaflet-bar leaflet-control leaflet-control-center");
        container.style.marginBottom = "10px"; 

        const btn = L.DomUtil.create("a", "", container);
        btn.href = "#";
        btn.innerHTML = `<svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="7"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="23" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="12" x2="1" y2="12"></line>
        </svg>`;
        btn.title = "Центрировать карту";
        btn.style.display = "flex";
        btn.style.alignItems = "center";
        btn.style.justifyContent = "center";
        btn.style.width = "30px";
        btn.style.height = "30px";

        L.DomEvent.on(btn, "click", function(e) {
          L.DomEvent.stopPropagation(e);
          L.DomEvent.preventDefault(e);
          if (initialBoundsRef.current) {
            map.fitBounds(initialBoundsRef.current, { padding: [30,30] });
          }
        });

        return container;
      }
    });

    new ResetControl({ position: "topleft" }).addTo(map);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        layerRef.current = null;
        initializedViewRef.current = false;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;
    const map = mapRef.current;

    if (layerRef.current) {
      map.removeLayer(layerRef.current);
      layerRef.current = null;
    }

    if (apiNodes.length === 0) return;

    const metricValues = apiNodes.map((node) => node.metric);
    const minValue = Math.min(...metricValues);
    const maxValue = Math.max(...metricValues);
    const valueRange = maxValue - minValue;

    const getColor = (value: number) => {
      const normalized = valueRange > 0 ? (value - minValue) / valueRange : 0.5;
      const c: [number, [number, number, number]][] = [
        [0.0, [0, 17, 255]],
        [0.25, [0, 255, 255]],
        [0.5, [255, 255, 0]],
        [0.75, [255, 123, 0]],
        [1.0, [255, 0, 0]],
      ];
      for (let i = 1; i < c.length; i++) {
        if (normalized <= c[i][0]) {
          const [r1, g1, b1] = c[i - 1][1];
          const [r2, g2, b2] = c[i][1];
          const t = (normalized - c[i - 1][0]) / (c[i][0] - c[i - 1][0]);
          const r = Math.round(r1 + (r2 - r1) * t);
          const g = Math.round(g1 + (g2 - g1) * t);
          const b = Math.round(b1 + (b2 - b1) * t);
          return `rgb(${r},${g},${b})`;
        }
      }
      return "rgb(255,0,0)";
    };

    const markers = apiNodes.map((node) => {
      const [lon, lat] = node.coordinates;
      return L.circleMarker([lat, lon], {
        radius: 6,
        fillColor: getColor(node.metric),
        color: "#000",
        weight: 0,
        opacity: 0.9,
        fillOpacity: 0.9,
      }).bindPopup(`
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${node.name || node.id}</div>
          <div><strong>${title}:</strong> ${node.metric.toFixed(6)}</div>
          <div><strong>Координаты:</strong> ${lat.toFixed(4)}, ${lon.toFixed(4)}</div>
        </div>
      `);
    });

    const group = L.featureGroup(markers);
    group.addTo(map);
    layerRef.current = group;

    if (!initializedViewRef.current && group.getLayers().length > 0) {
      const bounds = group.getBounds();
      map.fitBounds(bounds, { padding: [30, 30] });
      initializedViewRef.current = true;
      initialBoundsRef.current = bounds;
    }
  }, [apiNodes, metricType, title]);

  return (
    <Card className="absolute inset-0 w-full h-full overflow-hidden">
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />

      {apiNodes.length > 0 && (
        <div className="absolute bottom-5 left-5 bg-white p-3 rounded-lg shadow text-xs z-[600] pointer-events-auto">
          <div className="font-semibold">{title}</div>
          <div className="w-36 h-2 mt-1 rounded bg-gradient-to-r from-[#0011ff] via-[#ffff00] to-[#ff0000]" />
          <div className="flex justify-between text-gray-500 text-[10px] mt-1">
            <span>Low</span>
            <span>High</span>
          </div>
        </div>
      )}

      {apiNodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
          <div className="text-gray-500">Нет данных для отображения</div>
        </div>
      )}
    </Card>
  );
}