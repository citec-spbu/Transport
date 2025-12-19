import { useState, useEffect, useRef } from "react";
import cityUrls from "../data/city_urls.json";
import { Search } from "lucide-react";

interface CitySelectorProps {
  value: string;
  onChange: (city: string) => void;
}

type ListItemElement = HTMLLIElement;

export default function CitySelector({ value, onChange }: CitySelectorProps) {
  const [search, setSearch] = useState<string>("");
  const [filteredCities, setFilteredCities] = useState<string[]>([]);
  const [isListOpen, setIsListOpen] = useState<boolean>(false);

  const listRef = useRef<HTMLUListElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const allCities: string[] = Object.keys(cityUrls);

    if (search) {
      setFilteredCities(
        allCities.filter((city) =>
          city.toLowerCase().includes(search.toLowerCase())
        )
      );
      setIsListOpen(true); 
    } else {
      setFilteredCities(allCities);
      setIsListOpen(false); 
    }
  }, [search]);


  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isListOpen || !listRef.current) return;

      const items: NodeListOf<ListItemElement> =
        listRef.current.querySelectorAll("li");
      let focusedIndex: number = -1;

      items.forEach((item, index) => {
        if (item === document.activeElement) {
          focusedIndex = index;
        }
      });

      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          const nextItem = items[(focusedIndex + 1) % items.length];
          nextItem?.focus();
          break;

        case "ArrowUp":
          event.preventDefault();
          const prevItem =
            items[(focusedIndex - 1 + items.length) % items.length];
          prevItem?.focus();
          break;

        case "Enter":
          event.preventDefault();
          if (focusedIndex !== -1) {
            const selectedCity = items[focusedIndex].textContent || "";
            onChange(selectedCity);
            setSearch(selectedCity);
            setIsListOpen(false); 
            inputRef.current?.focus();
          }
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isListOpen, onChange, filteredCities]);


  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        listRef.current &&
        !listRef.current.contains(event.target as Node) &&
        inputRef.current !== event.target
      ) {
        setIsListOpen(false);
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value);
  };

  const handleInputClick = () => {
   
    if (!search) {
      setIsListOpen(true);
    }
  };

  const handleItemClick = (city: string) => {
    onChange(city);
    setSearch(city);
    setIsListOpen(false);
    inputRef.current?.focus();
  };

  return (
    <div className="max-w-md mx-auto mt-2 relative">
      <div className="relative">
        <div className="absolute inset-y-0 left-2 flex items-center">
          <Search className="text-gray-400" size={18} />
        </div>
        <input
          type="text"
          placeholder="Введите город"
          value={search}
          onChange={handleInputChange}
          onClick={handleInputClick}
          ref={inputRef}
          className="w-full pl-8 pr-2 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
        />
      </div>

      {isListOpen && (
        <ul
          ref={listRef}
          className={`
            border border-gray-300 rounded mt-1 max-h-60 overflow-y-auto bg-white shadow-md absolute w-full
            transition-all duration-300 ease-in-out
            ${isListOpen ? "opacity-100 scale-100" : "opacity-0 scale-95"}
          `}
        >
          {filteredCities.length === 0 ? (
            <li className="px-4 py-2 text-gray-500">Ничего не найдено</li>
          ) : (
            filteredCities.map((city) => (
              <li
                key={city}
                tabIndex={0}
                onClick={() => handleItemClick(city)}
                className={`
                  px-4 py-2 cursor-pointer hover:bg-blue-100
                  ${value === city ? "bg-blue-200 font-semibold" : ""}
                `}
              >
                {city}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
