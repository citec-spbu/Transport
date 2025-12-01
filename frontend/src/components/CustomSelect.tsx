import { useState, useRef, useEffect } from "react";
import Card from "./ui/Card";
import { ChevronDown } from "lucide-react";
interface Option {
  value: string;
  label: string;
}

interface CustomSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: Option[];
}

export default function CustomSelect({
  value,
  onChange,
  options,
}: CustomSelectProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const selectedLabel =
    options.find((o) => o.value === value)?.label || "Select...";

  return (
    <div ref={ref} className="relative">
      <Card
        className="cursor-pointer select-none flex justify-between items-center bg-white px-3 py-1.5"
        onClick={() => setOpen((p) => !p)}
      >
        <span className="text-sm pr-2">{selectedLabel}</span>
        <ChevronDown
          size={14}
          className={`text-gray-800 transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </Card>

      {open && (
        <Card className="absolute left-0 top-[110%] bg-white z-[2000] divide-y p-0">
          {options.map((opt) => (
            <div
              key={opt.value}
              className={`px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 ${
                value === opt.value ? "text-[#003A8C] font-sm" : ""
              }`}
              onClick={() => {
                onChange(opt.value);
                setOpen(false);
              }}
            >
              {opt.label}
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
