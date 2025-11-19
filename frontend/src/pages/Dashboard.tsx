import { useEffect, useState, useRef } from "react";
import Header from "../components/Header.tsx";
import MetricToggle from "../components/MetricToggle.tsx";
import ExportButton from "../components/ExportButton.tsx";
import StatsCard from "../components/StatsCard.tsx";
import Heatmap from "../components/Heatmap";
import HistogramWindow from "../components/HistogramWindow.tsx";
import { useParamsStore } from "../store/useParamStore";

export default function Dashboard() {
  const { city, transport, datasetId } = useParamsStore();

  const [analysisType, setAnalysisType] = useState<"pagerank" | "betweenness">("pagerank");

  const [nodes, setNodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedChart, setSelectedChart] = useState("histogram_pagerank");
  const heatmapRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  const chartOptions = [
    { value: "histogram_pagerank", label: "Гистограмма PageRank" },
    { value: "histogram_betweenness", label: "Гистограмма Betweenness" },
  ];

  // Debug logs
  console.log("City:", city);
  console.log("Transport:", transport);
  console.log("Analysis Type:", analysisType);
  console.log("Nodes:", nodes);

  // Загружаем данные с backend
  useEffect(() => {
    if (!datasetId) return;

    setLoading(true);

    fetch('/analysis/metric', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        datasetId,
        metric: analysisType
      })
    })
      .then(res => res.json())
      .then(data => {
        setNodes(data.nodes);
        setLoading(false);
      })
      .catch(err => {
        console.error("Ошибка загрузки данных:", err);
        setLoading(false);
      });
  }, [datasetId, analysisType]);


const stats = {
  city,
  pageRank: nodes.length > 0 ? Math.max(...nodes.map(n => n.pagerank ?? 0)) : 0,
  maxBetweenness: nodes.length > 0 ? Math.max(...nodes.map(n => n.betweenness ?? 0)) : 0,
  nodes: nodes.length,
  routes: nodes.length > 0 ? nodes.reduce((acc, n) => acc + (n.routesCount ?? 0), 0) : 0,
};

  const renderChart = () => {
    switch (selectedChart) {
      case "histogram_pagerank":
        return <HistogramWindow data={nodes} metricName="PageRank" />;
      case "histogram_betweenness":
        return <HistogramWindow data={nodes} metricName="Betweenness" />;
      default:
        return <HistogramWindow data={nodes} metricName="PageRank" />;
    }
  };

  const handleMetricToggleChange = (active: string) => {
    if (active === "PageRank" || active === "pagerank") {
      setAnalysisType("pagerank");
      setSelectedChart("histogram_pagerank");
    } else if (active === "Betweenness" || active === "betweenness") {
      setAnalysisType("betweenness");
      setSelectedChart("histogram_betweenness");
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <Header />

      <div className="px-4 py-3 flex justify-between items-center shrink-0">
        <MetricToggle selected={analysisType === "pagerank" ? "PageRank" : "Betweenness"} firstLabel="PageRank" secondLabel="Betweenness" onChange={handleMetricToggleChange} />
        <ExportButton
          nodes={nodes}
          stats={stats}
          heatmapRef={heatmapRef}
          chartRef={chartRef}
        />
      </div>

      <div className="flex justify-between items-stretch px-4 pb-4 flex-1 overflow-hidden">
        <div ref={heatmapRef} className="flex-1 mr-4 h-full">
          {loading ? (
            <p>Загрузка карты...</p>
          ) : nodes.length === 0 ? (
            <p>Данные отсутствуют для отображения карты.</p>
          ) : (
            <Heatmap
              nodes={nodes}
              title={analysisType === "pagerank" ? "PageRank Heatmap" : "Betweenness Heatmap"}
            />
          )}
        </div>

        <div className="w-[300px] flex flex-col space-y-3 overflow-y-auto">
          <StatsCard
            city={stats.city}
            pageRank={stats.pageRank}
            betweenness={stats.maxBetweenness}
            nodes={stats.nodes}
            routes={stats.routes}
          />

          <div>
            <label>Тип графика</label>
            <select
              value={selectedChart}
              onChange={(e) => setSelectedChart(e.target.value)}
            >
              {chartOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div ref={chartRef}>
            {loading ? (
              <p>Загрузка графика...</p>
            ) : nodes.length === 0 ? (
              <p>Данные отсутствуют для отображения графика.</p>
            ) : (
              renderChart()
            )}
          </div>
        </div>
      </div>
    </div>
  );
}