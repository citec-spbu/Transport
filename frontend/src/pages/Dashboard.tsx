import { useEffect, useState, useRef } from "react";
import Header from "../components/Header.tsx";
import MetricToggle from "../components/MetricToggle.tsx";
import ExportButton from "../components/ExportButton.tsx";
import StatsCard from "../components/StatsCard.tsx";
import Heatmap from "../components/Heatmap";
import HistogramWindow from "../components/HistogramWindow.tsx";
import { useParamsStore } from "../store/useParamStore";

export default function Dashboard() {
const {
  city,
  datasetId,
  datasetCache,
  metricType,
  setMetricType,
} = useParamsStore();

// метрики  для текущего datasetId
const metrics = datasetId ? datasetCache[datasetId]?.metrics : undefined;
const currentMetricData = metrics ? metrics[metricType] : undefined;
const nodes = currentMetricData?.nodes || [];
  const [selectedChart, setSelectedChart] = useState("histogram_pagerank");
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
    maxMetric: nodes.length > 0 ? Math.max(...nodes.map(n => n.metric ?? 0)) : 0,
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
            metricName={metricType === "pagerank" ? "PageRank" : "Betweenness"} 
            metricKey="metric"
          />
        );
    }
  };

 
  return (
    <div className="h-screen flex flex-col bg-[#F9FAFB]" key={datasetId}>
      <Header />

      <div className="px-4 py-3 flex justify-between items-center shrink-0">
        <MetricToggle 
          selected={metricType === "pagerank" ? "PageRank" : "Betweenness"} 
          firstLabel="PageRank" 
          secondLabel="Betweenness" 
          onChange={handleMetricToggleChange} 
        />
        <ExportButton
          nodes={nodes}
          stats={stats}
          heatmapRef={heatmapRef}
          chartRef={chartRef}

        />
      </div>

      <div className="flex justify-between items-stretch px-4 pb-4 flex-1 overflow-hidden">
        <div ref={heatmapRef} className="flex-1 mr-4 h-full bg-white rounded-xl shadow-sm">
          {nodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              {currentMetricData ? "Нет данных для отображения" : "Выберите метрику для анализа"}
            </div>
          ) : (
            <Heatmap
              key={`${datasetId}-${metricType}`} // Уникальный ключ для пересоздания карты
              nodes={nodes}
              metricType={metricType}
              title={metricType === "pagerank" ? "PageRank Heatmap" : "Betweenness Heatmap"}
            />
          )}
        </div>

        <div className="w-[300px] flex flex-col space-y-3 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-sm p-4">
            <StatsCard
              city={stats.city}
              maxMetric={stats.maxMetric}
              metricType={metricType}
              nodes={stats.nodes}
              routes={stats.routes}
            />
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип графика
            </label>
            <select
              value={selectedChart}
              onChange={(e) => setSelectedChart(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-[#003A8C] focus:border-[#003A8C]"
            >
              <option value="histogram_pagerank">Гистограмма PageRank</option>
              <option value="histogram_betweenness">Гистограмма Betweenness</option>
            </select>
          </div>

          <div ref={chartRef} className="bg-white rounded-xl shadow-sm p-4 flex-1">
            {nodes.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                {currentMetricData ? "Нет данных для графика" : "Выберите метрику для анализа"}
              </div>
            ) : (
              renderChart()
            )}
          </div>
        </div>
      </div>
    </div>
  );
}