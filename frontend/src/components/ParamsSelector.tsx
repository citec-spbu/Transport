import { useState } from "react";
import { useParamsStore } from "../store/useParamStore.ts";
import Card from "./ui/Card.tsx";
import CitySelector from "./CitySelector.tsx";
import DatasetList from "./DatasetList.tsx";

// Читаем актуальный токен непосредственно при запросе

export default function ParamsSelector() {
  const { city, transport, setAll, resetAnalysisData, bumpDatasetsRefresh } = useParamsStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const isValid = city.trim() !== "" && transport !== "";

  const handleSubmit = async () => {
    if (!isValid || isLoading) return;

    setIsLoading(true);
    setError("");
    resetAnalysisData();

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/v1/datasets/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...(token ? { Authorization: token } : {}),
        },
        body: JSON.stringify({ city, transport_type: transport }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 409) {
          setError("Датасет с таким городом и видом транспорта уже существует");
          return;
        }
        throw new Error(`HTTP error! status: ${res.status}, ${errorData.detail || "Unknown error"}`);
      }
      const data = await res.json();
      if (!data.dataset_id) throw new Error("Invalid response: dataset_id is missing");
      // Тригерим обновление списка датасетов
      bumpDatasetsRefresh();
    } catch (error) {
      console.error("Failed to load dataset:", error);
      setError(`Не удалось создать датасет: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto w-full">
      <h1 className="text-sm font-bold text-gray-900 mt-4 mb-1">Выберите параметры</h1>

      <Card className="p-6 max-h-[50vh] overflow-y-auto">
        <div className="mb-4">
          <h2 className="text-sm font-light text-gray-900 mb-1">Город</h2>
          <CitySelector
            value={city}
            onChange={(val) => {
              setAll({ city: val });
              resetAnalysisData();
            }}
          />
        </div>

        <div className="mb-2">
          <h2 className="text-sm font-light text-gray-900 mb-4">Вид транспорта</h2>
          <div className="space-y-3">
            {[
              { value: "bus", label: "Автобус" },
              { value: "trolleybus", label: "Троллейбус" },
              { value: "tram", label: "Трамвай" },
              { value: "metro", label: "Метро" },
            ].map(option => (
              <label key={option.value} className="flex items-center space-x-3 cursor-pointer group ml-2">
                <input
                  type="radio"
                  name="transport"
                  value={option.value}
                  checked={transport === option.value}
                  onChange={(e) => {
                    setAll({ transport: e.target.value });
                    resetAnalysisData();
                  }}
                  className="w-5 h-5 text-[#003A8C] border-gray-300 focus:ring-[#003A8C] cursor-pointer"
                />
                <span className="text-sm text-gray-900 group-hover:text-[#003A8C] transition-colors">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex justify-center mt-2">
          <button
            onClick={handleSubmit}
            disabled={!isValid || isLoading}
            className={`px-6 py-3 rounded-4xl font-medium text-sm transition-all duration-200 ${
              isValid && !isLoading
                ? "bg-[#003A8C] text-white hover:bg-[#002a6b] border border-[#003A8C]"
                : "bg-gray-100 text-gray-400 border border-gray-300 cursor-not-allowed"
            }`}
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.346 0 0 5.346 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.643z"
                  ></path>
                </svg>
                Загрузка данных
              </span>
            ) : (
              "Загрузить"
            )}
          </button>
        </div>
      </Card>
      
      {error && (
        <div className="mt-3 text-center text-sm text-red-600 font-medium">
          {error}
        </div>
      )}

      <DatasetList />
    </div>
  );
}
