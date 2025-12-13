import Header from "../components/Header.tsx";
import ExportButton from "../components/ExportButton.tsx";
import ClusteringMap from "../components/ClusteringMap.tsx";
import CityCard from "../components/CityCard.tsx";
import { useParamsStore } from "../store/useParamStore";
import { useEffect, useState, useRef } from "react"; 
import { Maximize2, Minimize2 } from "lucide-react";
import ClusterStatsCard from "../components/ClusterStatsCard.tsx";
import CustomSelect from "../components/CustomSelect.tsx";

/**
 * Render the clustering visualization page with controls for city and cluster type, an interactive map, export controls, and an optional statistics panel.
 *
 * @returns The React element for the clustering visualization page.
 */
export default function Clustering() {
  const { city, datasetId, clusterType, setClusterType, datasetCache } =
    useParamsStore();

  const currentCluster = datasetId
    ? datasetCache[datasetId]?.clusters?.[clusterType]
    : undefined;

  const [isFullscreen, setIsFullscreen] = useState(false);
  

  const mapRef = useRef<HTMLDivElement>(null);
  const statsCardRef = useRef<HTMLDivElement>(null);

  const handleClusterToggleChange = (active: string) => {
    if (active === "leiden" || active === "louvain") {
      setClusterType(active as "leiden" | "louvain");
    }
  };

  useEffect(() => {
   
  }, [clusterType]);

  return (
    
    <div className="h-screen w-screen relative overflow-hidden" key={datasetId}>
      

      <div className="relative z-10">
        <Header />

        <div className="px-4 py-1 flex items-center gap-3 justify-start pointer-events-auto w-fit">
          <div className="flex items-center shrink-0 gap-3">
            <CityCard city={city} />
            <CustomSelect
              value={clusterType}
              onChange={(v) => handleClusterToggleChange(v)}
              options={[
                { value: "leiden", label: "Leiden" },
                { value: "louvain", label: "Louvain" },
              ]}
            />
          </div>


          <ExportButton
            nodes={currentCluster?.nodes || []}
            stats={{
              city,
              nodes: currentCluster?.nodes?.length || 0,
              clusters: currentCluster?.nodes
                ? Array.from(
                    new Set(currentCluster.nodes.map((n: any) => n.cluster_id))
                  ).length
                : 0,
            }}
            heatmapRef={mapRef} 
            chartRef={statsCardRef} 
          />
        </div>
      </div>


      <div ref={mapRef} className="absolute inset-0 w-full h-full z-0">
        {currentCluster ? (
          <ClusteringMap data={currentCluster} clusterType={clusterType} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Загрузка данных
          </div>
        )}
      </div>

      
      <button
        onClick={() => setIsFullscreen(!isFullscreen)}
        className="absolute bottom-4 right-4 z-20 pointer-events-auto bg-white hover:bg-gray-100 rounded-lg shadow-lg p-2 transition-colors"
        title={isFullscreen ? "Показать панели" : "Полноэкранный режим"}
      >
        {isFullscreen ? (
          <Minimize2 className="w-5 h-5 text-gray-700" />
        ) : (
          <Maximize2 className="w-5 h-5 text-gray-700" />
        )}
      </button>

 
      {!isFullscreen && (
        <div
          ref={statsCardRef} 
          className="py-1 absolute right-4 top-15 z-10 pointer-events-none 
                w-[300px] max-h-[calc(100vh-100px)] overflow-y-auto flex flex-col space-y-3"
        >
          <div className="pointer-events-auto">
            <ClusterStatsCard stats={currentCluster?.statistics} />
          </div>
        </div>
      )}
    </div>
  );
}