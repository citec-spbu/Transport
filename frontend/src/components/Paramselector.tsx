import React from "react";
import { useParamsStore } from "../store/useParamStore";
import { useNavigate } from "react-router-dom";
import Card from "./ui/Card.tsx";
import CitySelector from "./CitySelector.tsx";

interface ParamsSelectorProps {
  onSubmit?: () => void;
}

export default function ParamsSelector({ onSubmit }: ParamsSelectorProps) {
  const { city, transport, setAll, resetAnalysisData } = useParamsStore();
  const navigate = useNavigate();

  const isValid = city.trim() !== "" && transport !== "";

  const handleSubmit = async () => {
    if (!isValid) return;

    // Очистка данных
    resetAnalysisData();

    try {
      const res = await fetch("http://localhost:8050/v1/datasets/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          city,
          transport_type: transport,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(
          `HTTP error! status: ${res.status}, ${
            errorData.detail || "Unknown error"
          }`
        );
      }

      const data = await res.json();

      if (!data.dataset_id) {
        throw new Error("Invalid response: dataset_id is missing");
      }

      setAll({
        city,
        transport,
        analysisType: "",
        datasetId: data.dataset_id,
      });

      navigate("/analysis");

      if (onSubmit) onSubmit();
    } catch (error) {
      console.error("Failed to load dataset:", error);
      alert(
        `Не удалось создать датасет: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    }
  };

  return (
    <div className="max-w-xl mx-auto w-full">
      <h1 className="text-sm font-bold text-gray-900 mt-8 mb-2">
        Выберите параметры
      </h1>

      <Card className="p-6">
        {/* Выбор города */}
        <div className="mb-10">
          <h2 className="text-sm font-light text-gray-900 mb-4">Город</h2>
          <CitySelector
            value={city}
            onChange={(val) => {
              if (val !== city) resetAnalysisData();
              setAll({ city: val });
            }}
          />
        </div>

        {/* Вид транспорта */}
        <div className="mb-10">
          <h2 className="text-sm font-light text-gray-900 mb-4">
            Вид транспорта
          </h2>
          <div className="space-y-3">
            {[
              { value: "bus", label: "Автобус" },
              { value: "trolleybus", label: "Троллейбус" },
              { value: "tram", label: "Трамвай" },
              { value: "metro", label: "Метро" },
            ].map((option) => (
              <label
                key={option.value}
                className="flex items-center space-x-3 cursor-pointer group ml-2"
              >
                <input
                  type="radio"
                  name="transport"
                  value={option.value}
                  checked={transport === option.value}
                  onChange={(e) => {
                    // Очищаем данные при смене транспорта
                    if (e.target.value !== transport) resetAnalysisData();
                    setAll({ transport: e.target.value });
                  }}
                  className="w-5 h-5 text-[#003A8C] border-gray-300 focus:ring-[#003A8C] cursor-pointer"
                />
                <span className="text-sm text-gray-900 group-hover:text-[#003A8C] transition-colors">
                  {option.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex justify-center mt-8">
          <button
            onClick={handleSubmit}
            disabled={!isValid}
            className={`px-6 py-3 rounded-4xl font-medium text-sm transition-all duration-200 ${
              isValid
                ? "bg-[#003A8C] text-white hover:bg-[#002a6b] border border-[#003A8C]"
                : "bg-gray-100 text-gray-400 border border-gray-300 cursor-not-allowed"
            }`}
          >
            {isValid ? "Далее" : "Заполните поля"}
          </button>
        </div>
      </Card>
    </div>
  );
}
