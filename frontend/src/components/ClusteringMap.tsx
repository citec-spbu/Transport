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
  nodesUrl: string;
  linksUrl: string;
  clusterType?: "leiden" | "louvain";
}

const ClusteringMap: React.FC<Props> = ({
  nodesUrl,
  linksUrl,
  clusterType = "leiden",
}) => {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const leafletMap = useRef<L.Map | null>(null);

  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [communities, setCommunities] = useState<
    Map<number, { color: string; count: number }>
  >(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showLegend, setShowLegend] = useState(false);

  //Load JSON
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError("");
      try {
        const [nodesRes, linksRes] = await Promise.all([
          fetch(nodesUrl),
          fetch(linksUrl),
        ]);
        if (!nodesRes.ok || !linksRes.ok) {
          throw new Error("Failed to fetch JSON files");
        }
        const nodesData: GraphNode[] = await nodesRes.json();
        const linksData: GraphLink[] = await linksRes.json();

        setNodes(nodesData);
        setLinks(linksData);
      } catch (err: any) {
        setError(err.message || "Error loading JSON");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [nodesUrl, linksUrl]);

  // Leaflet render
  useEffect(() => {
    if (!mapRef.current || nodes.length === 0) return;

    if (!leafletMap.current) {
      leafletMap.current = L.map(mapRef.current).setView([59.93, 30.3], 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
      }).addTo(leafletMap.current);
    }

    const map = leafletMap.current;

    map.eachLayer((layer) => {
      if (layer instanceof L.TileLayer) return;
      map.removeLayer(layer);
    });

    // Генерация цветов
    const communityColors = new Map<number, string>();
    const getColorForCommunity = (comm?: number): string => {
      if (!comm) return "#3A86FF";
      if (!communityColors.has(comm)) {
        const hue = (comm * 137.508) % 360;
        communityColors.set(comm, `hsl(${hue}, 70%, 55%)`);
      }
      return communityColors.get(comm)!;
    };

    // Подсчет сообществ
    const communityStats = new Map<number, { color: string; count: number }>();
    nodes.forEach((n) => {
      const comm =
        clusterType === "leiden" ? n.leiden_community : n.louvain_community;
      if (comm != null) {
        const color = getColorForCommunity(comm);
        const current = communityStats.get(comm);
        if (current) current.count++;
        else communityStats.set(comm, { color, count: 1 });
      }
    });
    setCommunities(communityStats);

    // ребра
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
          { color: "#888", weight: 1, opacity: 0.3 }
        ).addTo(map);
      });
    }
    //  узлы
    nodes.forEach((n) => {
      const comm =
        clusterType === "leiden" ? n.leiden_community : n.louvain_community;
      const color = getColorForCommunity(comm);
      const radius = n.pageRank ? 5 + Math.log(n.pageRank * 1000 + 1) * 2 : 6;

      L.circleMarker([n.lat, n.lon], {
        radius,
        color: "#000",
        weight: 1,
        fillColor: color,
        fillOpacity: 0.8,
      })
        .bindPopup(
          `
        <div style="font-family: sans-serif;">
          <div style="font-weight: bold; margin-bottom: 4px;">${n.name}</div>
          ${comm != null ? `<div>Community: ${comm}</div>` : ""}
          ${
            n.pageRank != null
              ? `<div>PageRank: ${n.pageRank.toFixed(4)}</div>`
              : ""
          }
        </div>
      `
        )
        .addTo(map);
    });

    const bounds = nodes
      .filter((n) => n.lat != null && n.lon != null)
      .map((n) => [n.lat, n.lon] as L.LatLngTuple);

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [nodes, links, clusterType]);

  if (loading) return <div className="p-4">Loading JSON...</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;

  return (
    <div className="w-full h-screen flex flex-col relative">
      <div className="p-4 flex justify-between gap-3">
        {/* информация Nodes и Links */}
        <div className="flex gap-3">
          {nodes.length > 0 && (
            <Card>
              <div className="text-sm text-gray-600">
                <span className="font-semibold">Nodes:</span> {nodes.length}
              </div>
            </Card>
          )}
          {clusterType === "louvain" && (
            <Card>
              <div className="text-sm text-gray-600">
                <span className="font-semibold">Links:</span> {links.length}
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
            <div className="font-bold mb-2">Communities</div>
            {Array.from(communities.entries())
              .sort((a, b) => a[0] - b[0])
              .map(([comm, { color, count }]) => (
                <div key={comm} className="flex items-center gap-2 mb-1">
                  <span
                    className="w-3 h-3 border border-black"
                    style={{ backgroundColor: color }}
                  />
                  <span>
                    Community {comm} ({count})
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
