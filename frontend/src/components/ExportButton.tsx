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
  heatmapRef,
  chartRef 
}: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
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

  const exportTXT = () => {
    try {
      const text = `
Transit Network Statistics
==========================
Export Date: ${new Date().toLocaleString()}

City: ${stats.city || "N/A"}
Average PageRank: ${stats.pageRank || "N/A"}
Max Betweenness: ${stats.maxBetweenness || "N/A"}
Number of Nodes: ${stats.nodes || "N/A"}
Number of Routes: ${stats.routes || "N/A"}

Total Data Points: ${nodes.length}
      `.trim();

      const blob = new Blob([text], { type: "text/plain;charset=utf-8;" });
      downloadFile(blob, "transit-network-stats.txt");
      setIsOpen(false);
    } catch (error) {
      console.error("Ошибка экспорта TXT:", error);
      alert("Ошибка при экспорте TXT");
    }
  };

  const exportHeatmapPDF = async () => {
    if (!heatmapRef?.current) {
      alert("Heatmap не найдена. Убедитесь, что карта загружена.");
      return;
    }

    setIsExporting(true);
    
    try {
      console.log("Начало экспорта Heatmap...");
      
      const html2canvas = (await import("html2canvas")).default;
      const { jsPDF } = await import("jspdf");

      const element = heatmapRef.current;
      
      console.log("Создание canvas...");
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        logging: false,
        backgroundColor: "#ffffff",
      });

      console.log("Canvas создан, размеры:", canvas.width, "x", canvas.height);

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: canvas.width > canvas.height ? "landscape" : "portrait",
        unit: "mm",
        format: "a4",
      });

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const imgWidth = pageWidth - 20;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      pdf.setFontSize(16);
      pdf.text("Transit Network Heatmap", pageWidth / 2, 15, { align: "center" });

      pdf.setFontSize(10);
      pdf.text(`Exported: ${new Date().toLocaleString()}`, pageWidth / 2, 22, { align: "center" });

      const yPos = 30;
      const maxHeight = pageHeight - yPos - 10;
      const finalHeight = Math.min(imgHeight, maxHeight);
      
      pdf.addImage(imgData, "PNG", 10, yPos, imgWidth, finalHeight);

      console.log("PDF создан, начало сохранения...");
      pdf.save("transit-network-heatmap.pdf");
      
      console.log("PDF успешно сохранён");
      setIsOpen(false);
    } catch (error) {
      console.error("Детальная ошибка экспорта PDF:", error);
      alert(`Ошибка при экспорте PDF: ${error instanceof Error ? error.message : "Неизвестная ошибка"}`);
    } finally {
      setIsExporting(false);
    }
  };

  const exportChartPDF = async () => {
    if (!chartRef?.current) {
      alert("График не найден");
      return;
    }

    setIsExporting(true);

    try {
      console.log("Начало экспорта графика...");
      
      const html2canvas = (await import("html2canvas")).default;
      const { jsPDF } = await import("jspdf");

      const element = chartRef.current;
      
      console.log("Создание canvas графика...");
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        allowTaint: true,
        logging: false,
        backgroundColor: "#ffffff",
      });

      console.log("Canvas создан, размеры:", canvas.width, "x", canvas.height);

      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      const pageWidth = pdf.internal.pageSize.getWidth();
      const imgWidth = pageWidth - 20;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;

      pdf.setFontSize(16);
      pdf.text("Transit Network Chart", pageWidth / 2, 15, { align: "center" });

      pdf.setFontSize(10);
      let yPos = 25;
      pdf.text(`City: ${stats.city || "N/A"}`, 10, yPos);
      yPos += 6;
      pdf.text(`Average PageRank: ${stats.pageRank || "N/A"}`, 10, yPos);
      yPos += 6;
      pdf.text(`Max Betweenness: ${stats.maxBetweenness || "N/A"}`, 10, yPos);
      yPos += 6;
      pdf.text(`Nodes: ${stats.nodes || "N/A"}`, 10, yPos);
      yPos += 6;
      pdf.text(`Routes: ${stats.routes || "N/A"}`, 10, yPos);
      yPos += 10;

      pdf.addImage(imgData, "PNG", 10, yPos, imgWidth, imgHeight);

      console.log("PDF создан, начало сохранения...");
      pdf.save("transit-network-chart.pdf");
      
      console.log("PDF успешно сохранён");
      setIsOpen(false);
    } catch (error) {
      console.error("Детальная ошибка экспорта PDF графика:", error);
      alert(`Ошибка при экспорте PDF: ${error instanceof Error ? error.message : "Неизвестная ошибка"}`);
    } finally {
      setIsExporting(false);
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
        <span className="text-[10px] font-light text-gray-800">
          {isExporting ? "Экспорт..." : "Экспорт данных"}
        </span>
        <ChevronDown size={13} className={`text-gray-800 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && !isExporting && (
        <div className="absolute right-0 mt-1 w-44 bg-white border border-[#E0E6EA] rounded-[8px] shadow-lg z-50">
          <div className="py-1">
            <div className="px-3 py-1 text-[9px] font-semibold text-gray-500 uppercase">Данные</div>
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
            <button
              onClick={exportTXT}
              className="w-full px-3 py-2 text-left text-[10px] hover:bg-gray-50 transition-colors flex items-center gap-2 border-b border-gray-100"
            >
              <Download size={12} className="text-gray-600" />
              <span>TXT статистика</span>
            </button>

            <div className="px-3 py-1 text-[9px] font-semibold text-gray-500 uppercase mt-1">Визуализация</div>
            <button
              onClick={exportHeatmapPDF}
              className="w-full px-3 py-2 text-left text-[10px] hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <Download size={12} className="text-gray-600" />
              <span>Heatmap PDF</span>
            </button>
            <button
              onClick={exportChartPDF}
              className="w-full px-3 py-2 text-left text-[10px] hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <Download size={12} className="text-gray-600" />
              <span>График PDF</span>
            </button>
          </div>
        </div>
      )}
        </Card>
      </div>
    );
}