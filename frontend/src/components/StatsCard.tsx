import React from "react";
import Card from "./ui/Card.tsx";
interface StatsCardProps {
  city: string;
  pageRank: number;
  betweenness: number;
  nodes: number;
  routes: number;
}

const StatsCard: React.FC<StatsCardProps> = ({
  city,
  pageRank,
  betweenness,
  nodes,
  routes,
}) => {
  return (
    <Card className="p-3 font-['Helvetica_Neue']">
      <div className="space-y-2">
        <div>
          <div className="text-[11px] text-[#6B7280]">Город</div>
          <div className="text-[12px] font-semibold text-[#111827]">{city}</div>
        </div>
        <div>
          <div className="text-[11px] text-[#6B7280]">Средний PageRank</div>
          <div className="text-[12px] font-semibold text-[#111827]">
            {pageRank}
          </div>
        </div>
        <div>
          <div className="text-[11px] text-[#6B7280]">
            Максимальный Betweenness
          </div>
          <div className="text-[12px] font-semibold text-[#111827]">
            {betweenness}
          </div>
        </div>
        <div>
          <div className="text-[11px] text-[#6B7280]">Количество узлов</div>
          <div className="text-[12px] font-semibold text-[#111827]">
            {nodes}
          </div>
        </div>
        <div>
          <div className="text-[11px] text-[#6B7280]">Количество маршрутов</div>
          <div className="text-[12px] font-semibold text-[#111827]">
            {routes}
          </div>
        </div>
      </div>
    </Card>
  );
};

export default StatsCard;