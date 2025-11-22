import Header from "../components/Header.tsx";
import ExportButton from "../components/ExportButton.tsx";
import MetricToggle from "../components/MetricToggle.tsx";
import ClusteringMap from "../components/ClusteringMap.tsx";
import CityCard from "../components/CityCard.tsx";
import { useParamsStore } from "../store/useParamStore";
import { useEffect } from "react";

export default function Clustering() {
  const { city, datasetId, clusterType, setClusterType, datasetCache } =
    useParamsStore();

  const currentCluster = datasetId
    ? datasetCache[datasetId]?.clusters?.[clusterType]
    : undefined;

  const selectedToggleValue = clusterType === "leiden" ? "Leiden" : "Louvain";

  const handleClusterToggleChange = (active: string) => {
    if (active === "Leiden" || active === "leiden") {
      setClusterType("leiden");
    } else if (active === "Louvain" || active === "louvain") {
      setClusterType("louvain");
    }
  };

  useEffect(() => {
    if (clusterType === "leiden") {
    } else if (clusterType === "louvain") {
    }
  }, [clusterType]);

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-sans">
      <Header />

      <div className="px-4 py-3 flex justify-between items-center shrink-0">
        <div className="flex items-center shrink-0 gap-3">
          <CityCard city={city} />
          <MetricToggle
            firstLabel="Leiden"
            secondLabel="Louvain"
            selected={selectedToggleValue}
            onChange={handleClusterToggleChange}
          />
        </div>

        <ExportButton />
      </div>

      <div className="flex-1 bg-white rounded-xl shadow-sm h-full mr-4 ml-4">
        {currentCluster ? (
          <ClusteringMap data={currentCluster} clusterType={clusterType} />
        ) : (
          <div className="p-4 text-gray-600">Загрузка данных</div>
        )}
      </div>
    </div>
  );
}
