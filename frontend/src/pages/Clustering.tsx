import { useState } from "react";
import Header from "../components/Header.tsx";
import ExportButton from "../components/ExportButton.tsx";
import MetricToggle from "../components/MetricToggle.tsx";
import ClusteringMap from "../components/ClusteringMap.tsx";
import CityCard from "../components/CityCard.tsx";

export default function Clustering() {
  const stats = {
    city: "Санкт-Петербург",
  };
  // Состояние для кластеризации
  const [clusterType, setClusterType] = useState<"leiden" | "louvain">(
    "leiden"
  );

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-sans">
      {/* Header */}
      <Header />

      <div className="px-4 py-3 flex justify-between items-center shrink-0">
        <div className="flex items-center shrink-0 gap-3">
          <CityCard city={stats.city} />
          <MetricToggle
            firstLabel="Leiden"
            secondLabel="Louvain"
            onChange={(value) => setClusterType(value as "leiden" | "louvain")}
          />
        </div>

        <ExportButton />
      </div>

      {/* Основное содержимое */}
      <div className="flex-1 bg-white rounded-xl shadow-sm h-full mr-4 ml-4">
        <ClusteringMap
          nodesUrl="/data/nodes_spb.json"
          linksUrl="/data/links_spb.json"
          clusterType={clusterType}
        />
      </div>
    </div>
  );
}
