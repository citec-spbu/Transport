import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import Card from "./ui/Card";

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

// --- Компонент ClusteringMap ---
const ClusteringMap: React.FC<Props> = ({ data, clusterType }) => {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const leafletMap = useRef<L.Map | null>(null);
  const markersLayer = useRef<L.LayerGroup | null>(null);
  const initialBoundsRef = useRef<L.LatLngBounds | null>(null);

  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [communities, setCommunities] = useState<
    Map<number, { color: string; count: number }>
  >(new Map());
  const [error, setError] = useState<string>("");
  const [showLegend, setShowLegend] = useState(false);

  useEffect(() => {
    try {
      const processedNodes = data.nodes.map((node) => ({
        id: node.id,
        name: node.name,
        lat: node.coordinates[1], // Latitude
        lon: node.coordinates[0], // Longitude
        clusterId: node.cluster_id,
      }));
      setNodes(processedNodes);
    } catch (err: any) {
      setError(err.message || "Error processing data");
    }
  }, [data]);

  useEffect(() => {
    if (!mapRef.current || leafletMap.current) return;

    const map = L.map(mapRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView([0, 0], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);

    markersLayer.current = L.layerGroup().addTo(map);
    leafletMap.current = map;

    const ResetControl = L.Control.extend({
      onAdd: function (map: L.Map) {
        const container = L.DomUtil.create(
          "div",
          "leaflet-bar leaflet-control leaflet-control-center"
        );

        const btn = L.DomUtil.create("a", "", container);
        btn.href = "#";
        btn.title = "Центрировать карту";

        btn.innerHTML = `<svg
          xmlns="www.w3.org"
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

        // Дополнительные стили для SVG внутри кнопки, чтобы она выглядела как в примере Heatmap
        btn.style.display = "flex";
        btn.style.alignItems = "center";
        btn.style.justifyContent = "center";
        btn.style.width = "30px";
        btn.style.height = "30px";


        L.DomEvent.on(btn, "click", (e) => {
          L.DomEvent.stopPropagation(e);
          L.DomEvent.preventDefault(e);
          if (initialBoundsRef.current) {

            map.fitBounds(initialBoundsRef.current, { padding: [30, 30] });
          }
        });

        return container;
      },
    });

   
    new ResetControl({ position: "topleft" }).addTo(map);

    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
      }
    };
  }, []);


  const firstFit = useRef(true);
  useEffect(() => {
    if (!leafletMap.current || !markersLayer.current) return;

    const map = leafletMap.current;
    const layer = markersLayer.current;

    layer.clearLayers();

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

    const markers = nodes.map((n) => {
      const color = getColorForCommunity(n.clusterId);
      return L.circleMarker([n.lat, n.lon], {
        radius: 6,
        color: "#000",
        weight: 0,
        fillColor: color,
        fillOpacity: 0.9,
      }).bindPopup(
        `
        <div style="font-family: sans-serif;">
          <div style="font-weight: bold; margin-bottom: 4px;">${
            n.name || n.id
          }</div>
          <div>Cluster: ${n.clusterId}</div>
          <div>Type: ${clusterType}</div>
        </div>
      `
      );
    });

 
    const group = L.featureGroup(markers);
    group.addTo(layer);


    if (firstFit.current && nodes.length > 0) {
      const bounds = group.getBounds();

      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [30, 30] });
        initialBoundsRef.current = bounds; 
        firstFit.current = false;
      }
    }
  }, [nodes, clusterType]);

  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;

  return (
  
    <div ref={mapRef} className="w-full h-full" />
  );
};

export default ClusteringMap;
