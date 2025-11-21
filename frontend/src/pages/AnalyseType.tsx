import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import AnalyseSelector from "../components/AnalyseSelector";
import { useParamsStore } from "../store/useParamStore";

export default function Analysis() {
  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#f8f9fa]">
      {/* Фоновая карта */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-6"
        style={{
          backgroundImage: "url('/images/background.png')",
        }}
      />

      <div className="relative z-10 flex flex-col h-full">
        <Header />

        {/* Основная часть */}
        <AnalyseSelector />
      </div>
    </div>
  );
}
