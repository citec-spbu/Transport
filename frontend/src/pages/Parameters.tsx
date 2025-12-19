import Header from "../components/Header";
import ParamsSelector from "../components/ParamsSelector";

export default function Parameters() {
  return (
    <div className="relative w-full h-screen overflow-auto bg-[#f8f9fa]">
      {/* Фоновая карта */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-6"
        style={{
          backgroundImage: "url('/images/background.png')",
        }}
      />

      <div className="relative z-10 flex flex-col h-full">
        <Header />
        <ParamsSelector />
      </div>
    </div>
  );
}