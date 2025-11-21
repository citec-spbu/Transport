import React from "react";
import Card from "./ui/Card.tsx";
interface HistogramData {
  range: string;
  count: number;
}

interface HistogramCardProps {
  title: string;
  data: HistogramData[];
}

const HistogramCard: React.FC<HistogramCardProps> = ({ title, data }) => {
  const maxCount = Math.max(...data.map((d) => d.count));

  return (
    <Card className=" p-6 ">
      <h3 className="text-[15px] font-semibold text-[#111827] mb-4">{title}</h3>

      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-3">
            <div className="w-20 text-[13px] text-[#4B5563]">{item.range}</div>
            <div className="flex-1 bg-[#E5E7EB] rounded-full h-6 relative overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 bg-[#1E40AF] rounded-full transition-all duration-500"
                style={{ width: `${(item.count / maxCount) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default HistogramCard;
