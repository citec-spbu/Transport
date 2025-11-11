import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Тип анализа</h1>
      <button
        onClick={() => navigate("/dashboard")}
        className="px-6 py-3 bg-[#003A8C] text-white font-medium rounded-xl shadow-md hover:bg-blue-800 transition"
      >
        Heatmap
      </button>

      <button
        onClick={() => navigate("/clustering")}
        className="px-6 py-3 bg-[#003A8C] text-white font-medium rounded-xl shadow-md hover:bg-blue-800 transition"
      >
        Кластеризация
      </button>
    </div>
  );
}
