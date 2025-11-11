import { useState, useEffect } from "react";

import Card from "./ui/Card.tsx";

interface MetricToggleProps {
  firstLabel: string;
  secondLabel: string;
  selected?: string;
  onChange?: (active: string) => void;
}

export default function MetricToggle({
  firstLabel,
  secondLabel,
  selected,
  onChange,
}: MetricToggleProps) {
  const [active, setActive] = useState(selected || firstLabel);

  useEffect(() => {
    if (selected) {
      setActive(selected);
    }
  }, [selected]);

  const handleClick = (label: string) => {
    setActive(label);
    if (onChange) onChange(label.toLowerCase());
  };

  return (
    <Card className="flex items-center gap-3 px-4 py-2 h-[45px]">
      <button
        onClick={() => handleClick(firstLabel)}
        className={`px-5 py-1.5 rounded-[6px] text-[10px] font-normal transition-all ${
          active === firstLabel
            ? "bg-[#003A8C] text-white"
            : "bg-[#F5F7FA] text-black"
        }`}
      >
        {firstLabel}
      </button>

      <button
        onClick={() => handleClick(secondLabel)}
        className={`px-5 py-1.5 rounded-[6px] text-[10px] font-normal transition-all ${
          active === secondLabel
            ? "bg-[#003A8C] text-white"
            : "bg-[#F5F7FA] text-black"
        }`}
      >
        {secondLabel}
      </button>
    </Card>
  );
}
