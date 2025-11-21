import React from "react";
import { useParamsStore } from "../store/useParamStore.ts";
import { useNavigate } from "react-router-dom";
import Card from "./ui/Card.tsx";

export default function AnalyseSelector() {
  const {
    analysisType,
    setAnalysisType,
    datasetId,
    datasetCache,
    setAnalysisData,
  } = useParamsStore();
  const navigate = useNavigate();

  const handleNext = async () => {
    if (!datasetId) {
      alert("Ошибка: dataset не загружен.");
      return;
    }

    if (!analysisType) {
      alert("Пожалуйста, выберите тип анализа.");
      return;
    }

    try {
      const cache = datasetCache[datasetId] || {};

      if (analysisType === "clustering") {
        if (!cache.clusters?.leiden || !cache.clusters?.louvain) {
          const methods = ["leiden", "louvain"];
          const clusters: Record<string, any> = {};

          for (const method of methods) {
            const res = await fetch(
              "http://localhost:8050/v1/analysis/cluster",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Accept: "application/json",
                },
                body: JSON.stringify({ dataset_id: datasetId, method }),
              }
            );

            if (!res.ok) {
              const errorData = await res.json().catch(() => ({}));
              throw new Error(
                `Ошибка кластеризации методом ${method}: ${
                  errorData.detail || res.statusText
                }`
              );
            }

            const data = await res.json();
            clusters[method] = data;
          }

          setAnalysisData(datasetId, { clusters });
        }

        navigate("/clustering");
      } else if (analysisType === "heatmap") {
        if (!cache.metrics?.pagerank || !cache.metrics?.betweenness) {
          const metrics = ["pagerank", "betweenness"];
          const metricsResults: Record<string, any> = {};

          for (const metric of metrics) {
            const res = await fetch(
              "http://localhost:8050/v1/analysis/metric",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Accept: "application/json",
                },
                body: JSON.stringify({ dataset_id: datasetId, metric }),
              }
            );

            if (!res.ok) {
              const errorData = await res.json().catch(() => ({}));
              throw new Error(
                `Ошибка вычисления метрики ${metric}: ${
                  errorData.detail || res.statusText
                }`
              );
            }

            const data = await res.json();
            metricsResults[metric] = data;
          }

          setAnalysisData(datasetId, { ...cache, metrics: metricsResults });
        }

        navigate("/dashboard");
      } else {
        throw new Error("Неизвестный тип анализа");
      }
    } catch (err) {
      console.error("Ошибка анализа:", err);
      alert(
        "Ошибка анализа: " + (err instanceof Error ? err.message : String(err))
      );
    }
  };

  const isValid = analysisType !== "";

  return (
    <div className="max-w-xl mx-auto w-full">
      <h1 className="text-sm font-bold text-gray-900 mt-8 mb-2">
        Выберите тип анализа
      </h1>

      <Card className="p-6">
        <div className="mb-10">
          <h2 className="text-sm font-light text-gray-900 mb-4">Тип анализа</h2>

          <div className="space-y-3">
            {[
              { value: "clustering", label: "Кластеризация (Leiden, Louvain)" },
              {
                value: "heatmap",
                label: "Тепловая карта (PageRank, Betweenness)",
              },
            ].map((option) => (
              <label
                key={option.value}
                className="flex items-center space-x-3 cursor-pointer group ml-2"
              >
                <input
                  type="radio"
                  name="analysis"
                  value={option.value}
                  checked={analysisType === option.value}
                  onChange={(e) => setAnalysisType(e.target.value)}
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
            onClick={handleNext}
            disabled={!isValid}
            className={`
              px-6 py-3 rounded-4xl font-medium text-sm transition-all duration-200
              ${
                isValid
                  ? "bg-[#003A8C] text-white hover:bg-[#002a6b] border border-[#003A8C]"
                  : "bg-gray-100 text-gray-400 border border-gray-300 cursor-not-allowed"
              }
            `}
          >
            {isValid ? "Далее" : "Выберите анализ"}
          </button>
        </div>
      </Card>
    </div>
  );
}
