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
  const mapRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (!mapRef.current || apiNodes.length === 0) return;
  if ((mapRef.current as any)._leaflet_id) {
    (mapRef.current as any)._leaflet_id = null;
  }
  const map = L.map(mapRef.current);

  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    {
      maxZoom: 18,
      opacity: 0.65,
      attribution: "© OpenStreetMap contributors",
    }
  ).addTo(map);

  // --- Сортировка узлов по метрике (по возрастанию) ---
  const sortedNodes = [...apiNodes].sort((a, b) => a.metric - b.metric);

  // --- Нормализация метрик для одинаковой шкалы ---
  const metricValues = apiNodes.map((node) => node.metric);
  const minValue = Math.min(...metricValues);
  const maxValue = Math.max(...metricValues);
  const valueRange = maxValue - minValue;

  const getColor = (value: number) => {
    const normalized = valueRange > 0 ? (value - minValue) / valueRange : 0.5;

    // Цветовая шкала
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

  const markers = sortedNodes.map((node) => {
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

  if (group.getLayers().length > 0) {
    map.fitBounds(group.getBounds(), { padding: [20, 20] });
  } else {
    map.setView([55.7558, 37.6173], 10);
  }

  return () => {
    group.clearLayers();
    map.remove();
  };
}, [apiNodes, metricType, title]);


  return (
    <Card className="relative w-full h-full overflow-hidden">
      <div ref={mapRef} className="w-full h-full" />

      {apiNodes.length > 0 && (
        <div className="absolute bottom-5 left-5 bg-white p-3 rounded-lg shadow text-xs z-[600]">
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