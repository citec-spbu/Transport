import { useEffect, useRef } from "react";
import L from "leaflet";
import Card from "./ui/Card";

type Node = {
  name: string;
  lat: number;
  lon: number;
  metric: number;
  norm: number;
};

export default function Heatmap({
  nodes,
  title,
}: {
  nodes: Node[];
  title: string;
}) {
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    const map = L.map(mapRef.current).setView([0, 0], 2);

    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
      {
        maxZoom: 18,
        opacity: 0.65,
      }
    ).addTo(map);

    const getColor = (v: number) => {
      const c: [number, [number, number, number]][] = [
        [0.0, [0, 17, 255]],
        [0.25, [0, 255, 255]],
        [0.5, [255, 255, 0]],
        [0.75, [255, 123, 0]],
        [1.0, [255, 0, 0]],
      ];

      for (let i = 1; i < c.length; i++) {
        if (v <= c[i][0]) {
          const [r1, g1, b1] = c[i - 1][1];
          const [r2, g2, b2] = c[i][1];
          const t = (v - c[i - 1][0]) / (c[i][0] - c[i - 1][0]);
          const r = Math.round(r1 + (r2 - r1) * t);
          const g = Math.round(g1 + (g2 - g1) * t);
          const b = Math.round(b1 + (b2 - b1) * t);
          return `rgb(${r},${g},${b})`;
        }
      }
      return "rgb(255,0,0)";
    };

    const markers = nodes.map((n) =>
      L.circleMarker([n.lat, n.lon], {
        radius: 5,
        fillColor: getColor(n.norm),
        color: getColor(n.norm),
        weight: 0.4,
        opacity: 0.8,
        fillOpacity: 0.8,
      }).bindPopup(`<b>${n.name}</b><br>${title}: ${n.metric.toFixed(6)}`)
    );

    const group = L.featureGroup(markers);
    group.addTo(map);
    map.fitBounds(group.getBounds());

    return () => {
      map.remove();
    };
  }, [nodes, title]);

  return (
    <Card className="relative w-full h-full">
      <div ref={mapRef} className="w-full h-full" />
      <div className="absolute bottom-5 left-5 bg-white p-3 rounded-lg shadow text-xs z-[600] opacity-100 mix-blend-normal">
        <div className="font-semibold">{title}</div>
        <div className="w-36 h-2 mt-1 rounded bg-gradient-to-r from-[#0011ff] via-[#ffff00] to-[#ff0000]" />
        <div className="flex justify-between text-gray-500 text-[10px] mt-1">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>
    </Card>
  );
}
