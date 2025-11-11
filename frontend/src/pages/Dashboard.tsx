import { useEffect, useState, useRef } from "react";
import Header from "../components/Header.tsx";
import MetricToggle from "../components/MetricToggle.tsx";
import ExportButton from "../components/ExportButton.tsx";
import StatsCard from "../components/StatsCard.tsx";
import Heatmap from "../components/Heatmap";
import HistogramWindow from "../components/HistogramWindow.tsx";

export default function Dashboard() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChart, setSelectedChart] = useState("histogram");
  const heatmapRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartOptions = [
    { value: "histogram_pagerank", label: "Гистограмма PageRank" },
    { value: "histogram_betweenness", label: "Гистограмма Betweenness" },
  ];

  useEffect(() => {
    fetch("/data/nodes.json")
      .then((res) => res.json())
      .then((data) => {
        setNodes(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Ошибка загрузки данных:", err);
        setLoading(false);
      });
  }, []);

  const stats = {
    city: "Санкт-Петербург",
    pageRank: 0.0048,
    maxBetweenness: 0.21,
    nodes: 3450,
    routes: 142,
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

  return (
    <div className="h-screen flex flex-col">
      <Header />

      <div className="px-4 py-3 flex justify-between items-center shrink-0">
        <MetricToggle firstLabel="PageRank" secondLabel="Betweenness" />
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
          ) : (
            <Heatmap nodes={nodes} title="PageRank Heatmap" />
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

          <div ref={chartRef}>{renderChart()}</div>
        </div>
      </div>
    </div>
  );
}
