import Card from "./ui/Card";
import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type ApiClusterNode = {
  id: string;
  name: string;
  cluster_id: number;
  coordinates: [number, number]; // [longitude, latitude]
};

type GraphNode = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  clusterId: number;
};

interface Props {
  data: {
    nodes: ApiClusterNode[];
  };
  clusterType: "leiden" | "louvain";
}

const ClusteringMap: React.FC<Props> = ({ data, clusterType }) => {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const leafletMap = useRef<L.Map | null>(null);

  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [communities, setCommunities] = useState<
    Map<number, { color: string; count: number }>
  >(new Map());
  const [error, setError] = useState<string>("");
  const [showLegend, setShowLegend] = useState(false);

  useEffect(() => {
    try {
      const processedNodes = data.nodes.map((node) => {
        return {
          id: node.id,
          name: node.name,
          lat: node.coordinates[1],
          lon: node.coordinates[0],
          clusterId: node.cluster_id,
        };
      });

      setNodes(processedNodes);
    } catch (err: any) {
      setError(err.message || "Error processing data");
    }
  }, [data, clusterType]);

  // Leaflet render
  useEffect(() => {
    if (!mapRef.current || nodes.length === 0) return;

    if (!leafletMap.current) {
      const firstNode = nodes[0];
      leafletMap.current = L.map(mapRef.current).setView(
        [firstNode.lat, firstNode.lon],
        11
      );
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors",
      }).addTo(leafletMap.current);
    }

    const map = leafletMap.current;

    map.eachLayer((layer) => {
      if (layer instanceof L.TileLayer) return;
      map.removeLayer(layer);
    });

    // Генерация цветов
    const communityColors = new Map<number, string>();
    const getColorForCommunity = (comm: number): string => {
      if (!communityColors.has(comm)) {
        const hue = (comm * 137.508) % 360;
        communityColors.set(comm, `hsl(${hue}, 70%, 55%)`);
      }
      return communityColors.get(comm)!;
    };

    const communityStats = new Map<number, { color: string; count: number }>();
    nodes.forEach((n) => {
      const color = getColorForCommunity(n.clusterId);
      const current = communityStats.get(n.clusterId);
      if (current) current.count++;
      else communityStats.set(n.clusterId, { color, count: 1 });
    });
    setCommunities(communityStats);

    // Узлы
    nodes.forEach((n) => {
      const color = getColorForCommunity(n.clusterId);
      const radius = 3;

      const popupContent = `
        <div style="font-family: sans-serif;">
          <div style="font-weight: bold; margin-bottom: 4px;">${
            n.name || n.id
          }</div>
          <div>Cluster: ${n.clusterId}</div>
          <div>Type: ${clusterType}</div>
        </div>
      `;

      L.circleMarker([n.lat, n.lon], {
        radius,
        color: "#000",
        weight: 0,
        fillColor: color,
        fillOpacity: 0.8,
      })
        .bindPopup(popupContent)
        .addTo(map);
    });

    const bounds = nodes
      .filter((n) => n.lat != null && n.lon != null)
      .map((n) => [n.lat, n.lon] as L.LatLngTuple);

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [nodes, clusterType]);

  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;

  return (
    <div className="w-full h-screen flex flex-col relative">
      <div className="p-4 flex justify-between gap-3">
        {/* информация Nodes */}
        <div className="flex gap-3">
          {nodes.length > 0 && (
            <Card className="p-2">
              <div className="text-xs text-gray-600">
                <span className="font-semibold">Nodes:</span> {nodes.length}
              </div>
            </Card>
          )}
          {communities.size > 0 && (
            <Card className="p-2">
              <div className="text-xs text-gray-600">
                <span className="font-semibold">Clusters:</span>{" "}
                {communities.size}
              </div>
            </Card>
          )}

        </div>
        {/* кнопка показать легенду */}
        <div>
          <button
            onClick={() => setShowLegend((prev) => !prev)}
            className="px-3 py-1.5 text-sm bg-[#003A8C] text-white rounded-md shadow-sm"
          >
            {showLegend ? "Скрыть легенду" : "Показать легенду"}
          </button>
        </div>
      </div>

      {/* Карта */}
      <div ref={mapRef} className="flex-1 relative">
        {showLegend && communities.size > 0 && (
          <div className="absolute bottom-4 right-4 bg-white p-3 rounded-lg shadow-lg z-1000 text-sm border border-[#E0E6EA]">
            <div className="font-bold mb-2">Communities ({clusterType})</div>
            {Array.from(communities.entries())
              .sort((a, b) => a[0] - b[0])
              .map(([comm, { color, count }]) => (
                <div key={comm} className="flex items-center gap-2 mb-1">
                  <span
                    className="w-3 h-3 border border-black"
                    style={{ backgroundColor: color }}
                  />
                  <span>
                    Cluster {comm} ({count})
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClusteringMap;
