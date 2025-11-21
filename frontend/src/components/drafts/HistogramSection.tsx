import { useEffect, useRef, useState } from "react";
import {
  Chart,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

interface DataPoint {
  name: string;
  metric: number;
  norm: number;
}

interface HistogramViewerProps {
  datasets: Record<string, DataPoint[]>;
}

export default function HistogramViewer({ datasets }: HistogramViewerProps) {
  const [selected, setSelected] = useState(Object.keys(datasets)[0]);
  const [windowSize, setWindowSize] = useState(50);
  const [startIndex, setStartIndex] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartRef = useRef<Chart | null>(null);

  const allData = datasets[selected];
  const total = allData.length;
  const maxValue = Math.max(...allData.map((d) => d.metric));

  function getColor(vNorm: number) {
    const c = [
      [0.0, [0, 17, 255]],
      [0.25, [0, 255, 255]],
      [0.5, [255, 255, 0]],
      [0.75, [255, 123, 0]],
      [1.0, [255, 0, 0]],
    ] as const;
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
  }

  function getWindowData(start: number, size: number) {
    const end = Math.min(total, start + size);
    const slice = allData.slice(start, end);
    return {
      labels: slice.map((d) => d.name),
      values: slice.map((d) => d.metric),
      colors: slice.map((d) => getColor(d.norm)),
    };
  }

  useEffect(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;

    const windowData = getWindowData(startIndex, windowSize);

    // уничтожаем старый график
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    chartRef.current = new Chart(ctx, {
      type: "bar",
      data: {
        labels: windowData.labels,
        datasets: [
          {
            label: selected,
            data: windowData.values,
            backgroundColor: windowData.colors,
            borderColor: "#444",
            borderWidth: 0.4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, max: maxValue * 1.05 },
          x: { ticks: { autoSkip: true, font: { size: 10 } } },
        },
        plugins: { legend: { display: false } },
      },
    });
  }, [selected, windowSize, startIndex]);

  return (
    <div className="p-6 bg-white border-2 border-[#E0E6EA] rounded-[11px] shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-800">Гистограмма метрик</h2>
        <select
          value={selected}
          onChange={(e) => {
            setSelected(e.target.value);
            setStartIndex(0);
          }}
          className="px-3 py-2 rounded-[8px] border border-[#E0E6EA] bg-[#F5F7FA] text-gray-800"
        >
          {Object.keys(datasets).map((key) => (
            <option key={key} value={key}>
              {key}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-4 text-sm text-gray-600">
        <span>Окно: {windowSize}</span>
        <input
          type="range"
          min={5}
          max={200}
          value={windowSize}
          onChange={(e) => setWindowSize(parseInt(e.target.value))}
          className="w-40 accent-[#003A8C]"
        />
        <span>Смещение: {startIndex}</span>
        <input
          type="range"
          min={0}
          max={Math.max(0, total - windowSize)}
          value={startIndex}
          onChange={(e) => setStartIndex(parseInt(e.target.value))}
          className="w-40 accent-[#003A8C]"
        />
      </div>

      <div className="h-[400px]">
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
}
