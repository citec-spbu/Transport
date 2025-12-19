import { useState, useEffect } from "react";
import Card from "./ui/Card.tsx";
import { useParamsStore } from "../store/useParamStore";
import { useNavigate } from "react-router-dom";

interface Dataset {
  dataset_id: string;
  city: string;
  transport_type: string;
}

interface DatasetListProps {
  onSelect?: () => void;
}

// Token will be read per request to avoid stale values

export default function DatasetList({ onSelect }: DatasetListProps) {
  const { setAll, datasetsRefreshToken } = useParamsStore();
  const navigate = useNavigate();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [isListLoading, setIsListLoading] = useState(false);

  const transportLabels: Record<string, string> = {
    bus: "Автобус",
    trolleybus: "Троллейбус",
    tram: "Трамвай",
    metro: "Метро",
  };

  // --- загрузка списка датасетов ---
  const loadDatasets = async () => {
    setIsListLoading(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/v1/datasets/", {
        headers: { ...(token ? { Authorization: token } : {}) },
      });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setDatasets(data.datasets || []);
    } catch (e) {
      console.error("Failed to load datasets:", e);
    } finally {
      setIsListLoading(false);
    }
  };

  // Load on mount
  useEffect(() => {
    loadDatasets();
  }, []);

  // Reload when store signals refresh (e.g., after auth or upload)
  useEffect(() => {
    if (datasetsRefreshToken > 0) {
      loadDatasets();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetsRefreshToken]);

  const handleDelete = async (datasetId: string) => {
    if (!confirm("Вы уверены, что хотите удалить этот датасет?")) return;

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/v1/datasets/${datasetId}`, {
        method: "DELETE",
        headers: { ...(token ? { Authorization: token } : {}) },
      });
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      setDatasets(datasets.filter(d => d.dataset_id !== datasetId));
    } catch (e) {
      console.error("Failed to delete dataset:", e);
      alert("Не удалось удалить датасет");
    }
  };

  const handleSelect = (dataset: Dataset) => {
    setAll({
      city: dataset.city,
      transport: dataset.transport_type,
      analysisType: "",
      datasetId: dataset.dataset_id,
    });
    navigate("/analysis");
    if (onSelect) onSelect();
  };

  return (
    <div className="max-w-xl mx-auto w-full">
      <h1 className="text-sm font-bold text-gray-900 mt-4 mb-1">Ваши загруженные датасеты</h1>
        <Card className="p-4 mt-2 max-h-60 overflow-y-auto">
        {isListLoading ? (
            <p>Загрузка...</p>
        ) : datasets.length === 0 ? (
            <p>Список пуст</p>
        ) : (
            <ul className="space-y-2">
            {datasets.map(d => (
                <li key={d.dataset_id} className="flex justify-between items-center p-2 border rounded">
                <div>
                    <p className="text-sm text-gray-600">
                    {d.city} — {transportLabels[d.transport_type] || d.transport_type}
                    </p>
                </div>
                <div className="flex space-x-2">
                    <button
                    onClick={() => handleSelect(d)}
                    className="px-3 py-1 text-sm bg-[#003A8C] text-white rounded hover:bg-[#002a6b] transition-colors"
                    >
                    Выбрать
                    </button>
                    <button
                    onClick={() => handleDelete(d.dataset_id)}
                    className="px-3 py-1 text-sm bg-[#003A8C] text-white rounded hover:bg-[#002a6b] transition-colors"
                    >
                    Удалить
                    </button>
                </div>
                </li>
            ))}
            </ul>
        )}
        </Card>
    </div>
  );
}
