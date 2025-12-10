import React from "react";
import Card from "./ui/Card.tsx";

interface StatsCardProps {
  city: string;
  maxMetric: number;
  metricType: "pagerank" | "betweenness";
  nodes: number;
  routes?: number;
}

const StatsCard: React.FC<StatsCardProps> = ({
  city,
  maxMetric,
  metricType,
  nodes,
  routes = 0,
}) => {
  // Форматирование чисел
  const formatMetric = (value: number): string => {
    if (value === 0) return "0";
    if (Math.abs(value) < 0.001) {
      return value.toExponential(2);
    }
    return value.toFixed(4);
  };

  const getMetricLabel = (): string => {
    switch (metricType) {
      case "pagerank":
        return "Максимальный PageRank";
      case "betweenness":
        return "Максимальный Betweenness";
      default:
        return "Максимальное значение";
    }
  };

  return (
    <Card className="p-3 font-sans">
      <div className="space-y-2">
        <div>
          <div className="text-[11px] text-gray-500 font-medium">Город</div>
          <div className="text-xs font-semibold text-gray-900 ">
            {city || "Не указан"}
          </div>
        </div>

        <div>
          <div className="text-[11px] text-gray-500 font-medium">
            {getMetricLabel()}
          </div>
          <div className="text-xs font-semibold text-gray-900 ">
            {formatMetric(maxMetric)}
          </div>
        </div>

        <div>
          <div className="text-[11px] text-gray-500 font-medium">
            Количество узлов
          </div>
          <div className="text-xs font-semibold text-gray-900">
            {nodes.toLocaleString()}
          </div>
        </div>

        {routes > 0 && (
          <div>
            <div className="text-[11px] text-gray-500 font-medium">
              Количество маршрутов
            </div>
            <div className="text-xs font-semibold text-gray-900 ">
              {routes.toLocaleString()}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default StatsCard;
