import Card from "./ui/Card.tsx";
import { Download, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface ExportButtonProps {
  nodes?: any[];
  stats?: any;
  heatmapRef?: React.RefObject<HTMLDivElement | null>;
  chartRef?: React.RefObject<HTMLDivElement | null>;
}

export default function ExportButton({ 
  nodes = [], 
  stats = {}, 
}: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const exportJSON = () => {
    try {
      const data = {
        stats,
        nodes,
        exportDate: new Date().toISOString(),
      };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      downloadFile(blob, "transit-network-data.json");
      setIsOpen(false);
    } catch (error) {
      console.error("Ошибка экспорта JSON:", error);
      alert("Ошибка при экспорте JSON");
    }
  };

  const exportCSV = () => {
    try {
      if (nodes.length === 0) {
        alert("Нет данных для экспорта");
        return;
      }

      const headers = Object.keys(nodes[0]).join(",");
      const rows = nodes.map(node => 
        Object.values(node).map(val => 
          typeof val === "string" && val.includes(",") ? `"${val}"` : val
        ).join(",")
      );
      const csv = [headers, ...rows].join("\n");

      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      downloadFile(blob, "transit-network-data.csv");
      setIsOpen(false);
    } catch (error) {
      console.error("Ошибка экспорта CSV:", error);
      alert("Ошибка при экспорте CSV");
    }
  };


  
  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

    return (
      <div ref={dropdownRef} className="relative">
        <Card className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className="flex items-center gap-1.5 px-3 py-1.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="text-[11px] font-light text-gray-800">
          {isExporting ? "Экспорт..." : "Экспорт данных"}
        </span>
        <ChevronDown size={13} className={`text-gray-800 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && !isExporting && (
        <div className="absolute right-0 mt-1 w-44 bg-white border border-[#E0E6EA] rounded-[8px] shadow-lg z-50">
          <div className="py-1">
           
            <button
              onClick={exportJSON}
              className="w-full px-3 py-2 text-left text-[10px] hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <Download size={12} className="text-gray-600" />
              <span>JSON формат</span>
            </button>
            <button
              onClick={exportCSV}
              className="w-full px-3 py-2 text-left text-[10px] hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <Download size={12} className="text-gray-600" />
              <span>CSV формат</span>
            </button>

          </div>
        </div>
      )}
        </Card>
      </div>
    );
}