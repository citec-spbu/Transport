import { useState } from "react";
import {
  Chart,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import { Maximize2, X } from "lucide-react";
import Card from "./ui/Card.tsx";

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip);

interface HistogramData {
  id: string;
  name: string;
  metric: number;
  norm: number;
}

interface HistogramWindowProps {
  data: HistogramData[];
  metricName?: string;
}

export default function HistogramWindow({
  data,
  metricName = "pageRank",
}: HistogramWindowProps) {
  const [windowSize, setWindowSize] = useState(50);
  const [startIndex, setStartIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const total = data.length;

  const getColor = (vNorm: number) => {
    const c: [number, [number, number, number]][] = [
      [0.0, [0, 17, 255]],
      [0.25, [0, 255, 255]],
      [0.5, [255, 255, 0]],
      [0.75, [255, 123, 0]],
      [1.0, [255, 0, 0]],
    ];
    for (let i = 1; i < c.length; i++) {
      if (vNorm <= c[i][0]) {
        const [r1, g1, b1] = c[i - 1][1];
        const [r2, g2, b2] = c[i][1];
        const t = (vNorm - c[i - 1][0]) / (c[i][0] - c[i - 1][0]);
        const r = Math.round(r1 + (r2 - r1) * t);
        const g = Math.round(g1 + (g2 - g1) * t);
        const b = Math.round(b1 + (b2 - b1) * t);
        return `rgb(${r},${g},${b})`;
      }
    }
    return "rgb(255,0,0)";
  };

  const getWindowData = () => {
    const end = Math.min(total, startIndex + windowSize);
    const windowData = data.slice(startIndex, end);
    return {
      labels: windowData.map((d) => d.name),
      values: windowData.map((d) => d.metric),
      colors: windowData.map((d) => getColor(d.norm)),
    };
  };

  const { labels, values, colors } = getWindowData();
  const maxValue = Math.max(...data.map((d) => d.metric)) * 1.05;

  const chartData = {
    labels,
    datasets: [
      {
        label: metricName,
        data: values,
        backgroundColor: colors,
        borderColor: "#444",
        borderWidth: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        ticks: {
          autoSkip: true,
          maxRotation: 60,
          font: { size: isModalOpen ? 11 : 8 },
        },
      },
      y: {
        beginAtZero: true,
        max: maxValue,
        title: {
          display: true,
          text: metricName,
          font: { size: isModalOpen ? 13 : 10 },
        },
        ticks: { font: { size: isModalOpen ? 11 : 9 } },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `${metricName}: ${ctx.parsed.y.toFixed(6)}`,
        },
      },
    },
  };

  const ControlsPanel = () => (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-600 w-16">Окно:</span>
        <input
          type="range"
          min={5}
          max={200}
          value={windowSize}
          onChange={(e) => {
            const newSize = Number(e.target.value);
            setWindowSize(newSize);
            if (startIndex > data.length - newSize) {
              setStartIndex(Math.max(0, data.length - newSize));
            }
          }}
          className="flex-1"
        />
        <span className="text-xs font-semibold text-gray-700 w-8 text-right">
          {windowSize}
        </span>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-600 w-16">Позиция:</span>
        <input
          type="range"
          min={0}
          max={Math.max(0, data.length - windowSize)}
          value={startIndex}
          onChange={(e) => setStartIndex(Number(e.target.value))}
          className="flex-1"
        />
        <span className="text-xs font-semibold text-gray-700 w-8 text-right">
          {startIndex}
        </span>
      </div>

      <div className="flex items-center justify-between gap-2">
        <div className="flex gap-1">
          <button
            onClick={() =>
              setStartIndex(
                Math.max(0, startIndex - Math.floor(windowSize / 4))
              )
            }
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            ←
          </button>
          <button
            onClick={() =>
              setStartIndex(
                Math.min(
                  data.length - windowSize,
                  startIndex + Math.floor(windowSize / 4)
                )
              )
            }
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
          >
            →
          </button>
        </div>
        <button
          onClick={() => {
            setWindowSize(50);
            setStartIndex(0);
          }}
          className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
        >
          Сброс
        </button>
      </div>
    </div>
  );

  return (
    <>

      <Card className="w-full flex flex-col gap-2 p-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-semibold text-gray-700">
            {metricName}
          </span>
          <button
            onClick={() => setIsModalOpen(true)}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
            title="Развернуть"
          >
            <Maximize2 size={16} className="text-gray-600" />
          </button>
        </div>

        <ControlsPanel />

        <div className="w-full h-[300px]">
          <Bar data={chartData} options={chartOptions} />
        </div>
      </Card>

      {isModalOpen && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#F9FAFB] bg-opacity-70 p-4">
          <Card className="w-[95vw] h-[90vh] flex flex-col">
            <div className="flex justify-between items-center p-4 border-b border-gray-200">
              <h2 className="text-lg font-bold text-gray-800">{metricName}</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X size={20} className="text-gray-600" />
              </button>
            </div>
            <div className="flex-1 p-6 overflow-auto flex flex-col gap-4">
              <ControlsPanel />
              <div className="flex-1 min-h-0">
                <Bar data={chartData} options={chartOptions} />
              </div>
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
