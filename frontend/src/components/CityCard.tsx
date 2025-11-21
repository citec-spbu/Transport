import React from "react";
import Card from "./ui/Card.tsx";
interface CityCardProps {
  city: string;
}

const CityCard: React.FC<CityCardProps> = ({ city }) => {
  return (
    <Card className=" pl-2 pr-10 py-2 h-[45px] flex flex-col items-start ">
      <div className="text-[9px] text-[#6B7280] ">Город</div>
      <div className="text-[11px] font-semibold text-[#111827] ">{city}</div>
    </Card>
  );
};

export default CityCard;
