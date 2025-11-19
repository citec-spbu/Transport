import { useEffect, useState } from "react";
import Header from "../components/Header.tsx";
import ExportButton from "../components/ExportButton.tsx";
import MetricToggle from "../components/MetricToggle.tsx";
import ClusteringMap from "../components/ClusteringMap.tsx";
import CityCard from "../components/CityCard.tsx";
import { useParamsStore } from "../store/useParamStore";

export default function Clustering() {
  const { city, transport, datasetId } = useParamsStore();

  const [clusterType, setClusterType] = useState<"leiden" | "louvain">("leiden");

  // Данные для карты
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(false);

  // Загружаем данные кластеризации
  useEffect(() => {
    if (!datasetId) return;

    setLoading(true);

    fetch("http://localhost:8000/analysis/cluster", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clusterType,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setNodes(data.nodes || []);
        setLinks([]);
      })
      .catch((err) => console.error("Cluster load error:", err))
      .finally(() => setLoading(false));
  }, [datasetId, clusterType]);

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-sans">
      <Header />

      <div className="px-4 py-3 flex justify-between items-center shrink-0">
        <div className="flex items-center shrink-0 gap-3">
          <CityCard city={city} />
          <MetricToggle
            firstLabel="Leiden"
            secondLabel="Louvain"
            onChange={(value) => setClusterType(value as "leiden" | "louvain")}
          />
        </div>

        <ExportButton />
      </div>

      <div className="flex-1 bg-white rounded-xl shadow-sm h-full mr-4 ml-4">
        {loading ? (
          <div className="p-4 text-gray-600">Загрузка кластеризации...</div>
        ) : (
          <ClusteringMap nodes={nodes} links={links} clusterType={clusterType} />
        )}
      </div>
    </div>
  );
}