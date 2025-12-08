import { useEffect, useState, useRef } from "react";
import Header from "../components/Header.tsx";
import ExportButton from "../components/ExportButton.tsx";
import StatsCard from "../components/StatsCard.tsx";
import Heatmap from "../components/Heatmap";
import HistogramWindow from "../components/HistogramWindow.tsx";
import { useParamsStore } from "../store/useParamStore";
import CustomSelect from "../components/CustomSelect.tsx";
import { Maximize2, Minimize2 } from "lucide-react";

export default function Dashboard() {
  const { city, datasetId, datasetCache, metricType, setMetricType } =
    useParamsStore();

  const metrics = datasetId ? datasetCache[datasetId]?.metrics : undefined;
  const currentMetricData = metrics ? metrics[metricType] : undefined;
  const nodes = currentMetricData?.nodes || [];
  const [selectedChart, setSelectedChart] = useState("histogram_pagerank");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const heatmapRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (metricType === "pagerank") {
      setSelectedChart("histogram_pagerank");
    } else {
      setSelectedChart("histogram_betweenness");
    }
  }, [metricType]);

  const handleMetricToggleChange = (active: string) => {
    if (active === "PageRank" || active === "pagerank") {
      setMetricType("pagerank");
      setSelectedChart("histogram_pagerank");
    } else if (active === "Betweenness" || active === "betweenness") {
      setMetricType("betweenness");
      setSelectedChart("histogram_betweenness");
    }
  };

  const stats = {
    city,
    maxMetric:
      nodes.length > 0 ? Math.max(...nodes.map((n) => n.metric ?? 0)) : 0,
    nodes: nodes.length,
    routes: 0,
  };

  const renderChart = () => {
    if (!currentMetricData || nodes.length === 0) {
      return <p className="text-gray-500">Нет данных для графика</p>;
    }

    switch (selectedChart) {
      case "histogram_pagerank":
        return (
          <HistogramWindow
            data={nodes}
            metricName="PageRank"
            metricKey="metric"
          />
        );
      case "histogram_betweenness":
        return (
          <HistogramWindow
            data={nodes}
            metricName="Betweenness"
            metricKey="metric"
          />
        );
      default:
        return (
          <HistogramWindow
            data={nodes}
            metricName={
              metricType === "pagerank" ? "PageRank" : "Betweenness"
            }
            metricKey="metric"
          />
        );
    }
  };

  return (
    <div className="h-screen w-screen relative overflow-hidden" key={datasetId}>
      {/* Header and controls - hide in fullscreen */}
      {!isFullscreen && (
        <div className="relative z-10 pointer-events-none">
          <div className="pointer-events-auto">
            <Header />
          </div>

          <div className="px-4 py-1 flex items-center gap-3 justify-start pointer-events-auto w-fit">
            <CustomSelect
              value={metricType}
              onChange={(v) => handleMetricToggleChange(v)}
              options={[
                { value: "pagerank", label: "PageRank" },
                { value: "betweenness", label: "Betweenness" },
              ]}
            />
            <ExportButton
              nodes={nodes}
              stats={stats}
              heatmapRef={heatmapRef}
              chartRef={chartRef}
            />
          </div>
        </div>
      )}

      {/* Heatmap - always visible */}
      <div ref={heatmapRef} className="absolute inset-0 w-full h-full z-0">
        {nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            {currentMetricData
              ? "Нет данных для отображения"
              : "Выберите метрику для анализа"}
          </div>
        ) : (
          <Heatmap
            key={`${datasetId}-${metricType}`}
            nodes={nodes}
            metricType={metricType}
            title={
              metricType === "pagerank"
                ? "PageRank"
                : "Betweenness"
            }
          />
        )}
      </div>

      {/* Fullscreen toggle button - always visible */}
      
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

      {/* Stats and chart - hide in fullscreen */}
      {!isFullscreen && (
        <div className="py-1 absolute right-4 top-15 z-10 pointer-events-none w-[300px] overflow-y-auto flex flex-col space-y-3">
          <div className="pointer-events-auto">
            <StatsCard
              city={stats.city}
              maxMetric={stats.maxMetric}
              metricType={metricType}
              nodes={stats.nodes}
              routes={stats.routes}
            />
          </div>

          <div
            ref={chartRef}
            className="w-full pointer-events-auto"
          >
            {nodes.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                {currentMetricData
                  ? "Нет данных для графика"
                  : "Выберите метрику для анализа"}
              </div>
            ) : (
              renderChart()
            )}
          </div>
        </div>
      )}
    </div>
  );
}