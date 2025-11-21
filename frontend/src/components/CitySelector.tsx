import React, { useState, useEffect } from "react";
import cityUrls from "../../../cache/cities/city_urls.json";
import { Search } from "lucide-react";

interface CitySelectorProps {
  value: string;
  onChange: (city: string) => void;
}

export default function CitySelector({ value, onChange }: CitySelectorProps) {
  const [search, setSearch] = useState("");
  const [filteredCities, setFilteredCities] = useState<string[]>([]);

  useEffect(() => {
    const allCities = Object.keys(cityUrls);
    setFilteredCities(
      allCities.filter((c) =>
        c.toLowerCase().includes(search.toLowerCase())
      )
    );
  }, [search]);

  return (
    <div className="max-w-md mx-auto mt-4">
      <label className="block text-sm font-light text-gray-900 mb-2">
        Город
      </label>
      <div className="relative">
        <Search className="absolute top-2 left-2 text-gray-400" size={18} />
        <input
          type="text"
          placeholder="Поиск города..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-8 pr-2 py-2 border border-gray-300 rounded"
        />
      </div>

      <ul className="border border-gray-300 rounded mt-2 max-h-60 overflow-y-auto">
        {filteredCities.map((c) => (
          <li
            key={c}
            onClick={() => onChange(c)}
            className={`px-4 py-2 cursor-pointer hover:bg-blue-100 ${
              value === c ? "bg-blue-200 font-semibold" : ""
            }`}
          >
            {c}
          </li>
        ))}
      </ul>
    </div>
  );
}