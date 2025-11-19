import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import PrimaryButton from "../components/PrimaryButton";
export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#f8f9fa]">
      {/* Фоновая карта */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-6"
        style={{
          backgroundImage: "url('images/background.png')",
        }}
      />

      {/* Контент поверх фона */}
      <div className="relative z-10 flex flex-col h-full">
        {/* Header */}
        <Header />

        {/* Центрированный блок */}
        <div className="flex flex-col items-center justify-center flex-1 text-center px-4">
          <h1 className="text-8xl font-medium text-black ">
            Transit Network
          </h1>

          <p className="mt-3 text-gray-600 text-lg">
            Сервис <span className="font-semibold text-black">анализа</span>{" "}
            общественного транспорта города
          </p>

          <PrimaryButton onClick={() => navigate("/parameters")} className="mt-8 px-20 py-3 text-2xl">
            Начать
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
}
