import Card from "./ui/Card";
import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type GraphNode = {
  id: string;
  lat: number;
  lon: number;
  name?: string;
  leiden_community?: number;
  louvain_community?: number;
  pageRank?: number;
};

type GraphLink = {
  source: string;
  target: string;
};

interface Props {
  nodes: GraphNode[];
  links: GraphLink[];
  clusterType: "leiden" | "louvain";
}

const ClusteringMap: React.FC<Props> = ({
  nodes,
  links,
  clusterType = "leiden",
}) => {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const leafletMap = useRef<L.Map | null>(null);

  const [communities, setCommunities] = useState<
    Map<number, { color: string; count: number }>
  >(new Map());

  const [showLegend, setShowLegend] = useState(false);

  // Leaflet render
  useEffect(() => {
    if (!mapRef.current || nodes.length === 0) return;

    // Инициализация карты
    if (!leafletMap.current) {
      leafletMap.current = L.map(mapRef.current).setView([59.93, 30.3], 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
      }).addTo(leafletMap.current);
    }

    const map = leafletMap.current;

    // Удаляем старые слои
    map.eachLayer((layer) => {
      if (layer instanceof L.TileLayer) return;
      map.removeLayer(layer);
    });

    // Цвета
    const communityColors = new Map<number, string>();
    const getColorForCommunity = (comm?: number): string => {
      if (!comm) return "#3A86FF";
      if (!communityColors.has(comm)) {
        const hue = (comm * 137.508) % 360;
        communityColors.set(comm, `hsl(${hue}, 70%, 55%)`);
      }
      return communityColors.get(comm)!;
    };

    // Подсчёт сообществ
    const stats = new Map<number, { color: string; count: number }>();
    nodes.forEach((n) => {
      const comm =
        clusterType === "leiden" ? n.leiden_community : n.louvain_community;

      if (comm != null) {
        const color = getColorForCommunity(comm);
        const existing = stats.get(comm);
        if (existing) existing.count++;
        else stats.set(comm, { color, count: 1 });
      }
    });

    setCommunities(stats);

    // Рёбра (только louvain)
    if (clusterType === "louvain") {
      links.forEach((l) => {
        const a = nodes.find((x) => x.id === l.source);
        const b = nodes.find((x) => x.id === l.target);
        if (!a || !b) return;

        L.polyline(
          [
            [a.lat, a.lon],
            [b.lat, b.lon],
          ],
          { color: "#999", weight: 1, opacity: 0.3 }
        ).addTo(map);
      });
    }

    // Узлы
    nodes.forEach((n) => {
      const comm =
        clusterType === "leiden" ? n.leiden_community : n.louvain_community;
      const color = getColorForCommunity(comm);

      L.circleMarker([n.lat, n.lon], {
        radius: 4,
        fillColor: color,
        fillOpacity: 0.85,
        stroke: false,
      })
        .bindPopup(
          `
        <div style="font-family: sans-serif;">
          <b>${n.name ?? "Нет имени"}</b>
          ${comm != null ? `<div>Community: ${comm}</div>` : ""}
          ${n.pageRank ? `<div>PageRank: ${n.pageRank.toFixed(4)}</div>` : ""}
        </div>
        `
        )
        .addTo(map);
    });

    // Авто зум
    const bounds = nodes
      .map((n) => [n.lat, n.lon] as [number, number])
      .filter((coord) => coord[0] && coord[1]);

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [nodes, links, clusterType]);

  return (
    <div className="w-full h-full flex flex-col relative">
      {/* Верхняя панель */}
      <div className="p-4 flex justify-between gap-3">
        <div className="flex gap-3">
          <Card>
            <div className="text-xs text-gray-600 p-2">
              <span className="font-semibold">Nodes:</span> {nodes.length}
            </div>
          </Card>

          {clusterType === "louvain" && (
            <Card>
              <div className="text-xs text-gray-600 p-2">
                <span className="font-semibold">Links:</span> {links.length}
              </div>
            </Card>
          )}
        </div>

        {/* Кнопка легенды */}
        <button
          onClick={() => setShowLegend((prev) => !prev)}
          className="px-3 py-1.5 text-sm bg-[#003A8C] text-white rounded-md shadow-sm"
        >
          {showLegend ? "Скрыть легенду" : "Показать легенду"}
        </button>
      </div>

      {/* Карта */}
      <div ref={mapRef} className="flex-1 relative">
        {showLegend && communities.size > 0 && (
          <div className="absolute bottom-4 right-4 bg-white p-3 rounded-lg shadow-lg z-[1000] text-sm border border-[#E0E6EA]">
            <div className="font-bold mb-2">Communities</div>

            {Array.from(communities.entries())
              .sort((a, b) => a[0] - b[0])
              .map(([comm, { color, count }]) => (
                <div key={comm} className="flex items-center gap-2 mb-1">
                  <span
                    className="w-3 h-3 border border-black"
                    style={{ backgroundColor: color }}
                  />
                  Community {comm} ({count})
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClusteringMap;
