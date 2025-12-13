import datetime
import json
import math
import os
import random
import re
import time
from abc import abstractmethod
from urllib.parse import urljoin

import requests
import requests_cache
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

"""
    Класс занимающийся парсингом данных с сайта https://kudikina.ru
"""

# === Global Settings ===
SITE_URL = "https://kudikina.ru/"
MAP_URL = "/map"
TIMETABLE_FORWARD_URL = "/A"
TIMETABLE_BACKWARD_URL = "/B"
CACHE_EXPIRE_DAYS = 30
REQUEST_PAUSE_SEC = 2

# --- Cache Configuration ---
BASE_CACHE_DIR = "./cache"
CITY_CACHE_DIR = os.path.join(BASE_CACHE_DIR, "cities")
session = requests_cache.CachedSession(
    cache_name=os.path.join(BASE_CACHE_DIR, "http_cache"),
    expire_after=datetime.timedelta(days=30),
)
retries = Retry(total=5, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)


class AbstractTransportGraphParser:
    def __init__(self, city_name):
        """Инициализирует парсер для указанного города."""
        self.city_name = city_name
        self.city_url = self.__get_city_url()
        self.nodes = {}
        self.relationships = []
        self.transport_url = self.get_transport_url()
        self.transport_class = self.get_transport_class()
        self.city_dir = os.path.join(
            BASE_CACHE_DIR,
            "routes_data",
            self.city_name.lower(),
            self.transport_url.strip("/"),
        )
        os.makedirs(self.city_dir, exist_ok=True)

    # === Main Method ===
    def parse(self, use_cache=True):
        """Парсит все маршруты города и формирует граф."""
        if not self.city_url:
            print(f"[ERROR] City URL for '{self.city_name}' not found. Aborting.")
            return None, None

        transport_type = self.transport_url.strip("/")
        print(
            f"[INFO] Starting parsing for city: {self.city_name} (Transport: {transport_type})"
        )

        routes_index_path = os.path.join(self.city_dir, "routes_index.json")
        if use_cache and self.__is_cache_fresh(routes_index_path):
            with open(routes_index_path, "r", encoding="utf-8") as f:
                all_routes = json.load(f)
            print("[INFO] Route index loaded from cache.")
        else:
            all_routes = self.get_all_routes_info()
            self.__save_json(routes_index_path, all_routes)
            print("[INFO] Fetched and saved new route index.")

        for route_number, route_name, route_url in all_routes:
            route_path = self.__get_route_path(route_number)
            if use_cache and self.__is_cache_fresh(route_path):
                with open(route_path, "r", encoding="utf-8") as f:
                    route_data = json.load(f)
                self.__merge_route_data(route_data)
                print(f"[CACHE] Loaded route '{route_number}' from cache.")
                continue

            route_data = self.__parse_single_route(route_number, route_url)
            if not route_data:
                continue  # Логирование происходит внутри __parse_single_route

            self.__save_json(route_path, route_data)
            self.__merge_route_data(route_data)
            print(f"[FETCH] Parsed and cached route: '{route_number}'")
            time.sleep(REQUEST_PAUSE_SEC + random.uniform(0.3, 1.2))

        print(f"[SUCCESS] Parsing complete for {self.city_name} ({transport_type}).")
        print(
            f"[STATS] Total routes: {len(all_routes)}, Nodes: {len(self.nodes)}, Relationships: {len(self.relationships)}"
        )
        return self.nodes, self.relationships

    # === Single Route Processing ===
    def __parse_single_route(self, route_number, route_url):
        """Парсит один маршрут: расписание, координаты, узлы и связи."""
        timetable, success = self.get_timetable(route_url)

        if not success or not timetable:
            print(f"[WARN] Skipping route '{route_number}': Failed to parse timetable.")
            return None

        stop_coords = self.get_stop_coordinates(route_url)
        if not stop_coords:
            print(
                f"[WARN] No coordinates found for route '{route_number}'. Proceeding with approximations."
            )

        route_nodes, route_relationships = {}, []
        last_coordinate = None
        previous_stop = None
        previous_time = None

        for row in timetable:
            stop_name = row["stopName"]
            time_point = row["timePoint"]

            coordinate = self.__get_filled_coordinate(
                stop_coords, stop_name, last_coordinate
            )
            if coordinate is None:
                print(
                    f"[WARN] Skipping stop '{stop_name}' in route '{route_number}': No coordinate available."
                )
                continue
            node_name, _ = self.__check_and_find_unique_stop(
                stop_name, coordinate, route_nodes
            )

            node = {
                "name": node_name,
                "routeList": [route_number],
                "xCoordinate": coordinate.x,
                "yCoordinate": coordinate.y,
                "isCoordinateApproximate": coordinate.is_approximate,
            }
            route_nodes[node_name] = node

            if previous_stop and previous_stop["name"] != node_name:
                duration = self.calculate_duration(previous_time, time_point)
                if duration is not False and duration > 0:  # !!! Не пропускаем 0
                    relationship_name = f"{previous_stop['name']} -> {node_name}; route_name: {route_number}"
                    route_relationships.append(
                        {
                            "startStop": previous_stop["name"],
                            "endStop": node_name,
                            "name": relationship_name,
                            "route": route_number,
                            "duration": duration,
                        }
                    )

            last_coordinate = coordinate
            previous_stop = node
            previous_time = time_point

        return {
            "routeNumber": route_number,
            "routeUrl": route_url,
            "nodes": route_nodes,
            "relationships": route_relationships,
            "timetable": timetable,
            "coordinates": {k: v.__dict__ for k, v in stop_coords.items()},
            "timestamp": datetime.datetime.now().isoformat(),
        }

    # === Coordinate Helpers ===
    def __get_filled_coordinate(self, stop_coordinates, stop_name, last_coordinate):
        """Возвращает координату остановки, при отсутствии берёт предыдущую."""
        coordinate = stop_coordinates.get(stop_name)
        if coordinate is None or not coordinate.is_defined():
            if last_coordinate is None:
                return None
            else:
                return Coordinate(last_coordinate.x, last_coordinate.y, True)
        return coordinate

    # === Caching Logic ===
    def __get_route_path(self, route_number):
        """Строит путь к файлу кеша для маршрута."""
        safe_name = re.sub(r"[^a-zA-Zа-яА-Я0-9_-]", "_", route_number)
        return os.path.join(self.city_dir, f"{safe_name}.json")

    def __is_cache_fresh(self, path):
        """Проверяет, не устарел ли кеш по пути."""
        if not os.path.exists(path):
            return False
        mtime = os.path.getmtime(path)
        age_in_days = (
            datetime.datetime.now() - datetime.datetime.fromtimestamp(mtime)
        ).days
        return age_in_days <= CACHE_EXPIRE_DAYS

    def __save_json(self, path, data):
        """Сохраняет данные в JSON по указанному пути."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def __merge_route_data(self, route_data):
        """Объединяет узлы и связи маршрута с общими структурами."""
        for name, node in route_data.get("nodes", {}).items():
            if name not in self.nodes:
                self.nodes[name] = node
            else:
                for r in node.get("routeList", []):
                    if r not in self.nodes[name].get("routeList", []):
                        self.nodes[name]["routeList"].append(r)

        for rel in route_data.get("relationships", []):
            if rel.get("duration") and rel["duration"] > 0:
                self.relationships.append(rel)

    # === City URL Management ===
    def __get_city_url(self):
        """Возвращает URL страницы города, используя кеш или парсинг."""
        cache_path = os.path.join(CITY_CACHE_DIR, "city_urls.json")
        cities = self.load_cache(cache_path)
        if not cities:
            print(
                "[INFO] City URL cache is empty or expired. Refetching from the source."
            )
            cities = self.parse_all_city_urls()
            self.save_cache(cache_path, cities)
        return cities.get(self.city_name)

    def parse_all_city_urls(self):
        """Парсит список всех городов и их относительные URL."""
        print(f"[INFO] Parsing all city URLs from {SITE_URL}...")
        try:
            response = session.get(SITE_URL, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch main page: {e}")
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        cities = {}

        for ul in soup.find_all("ul", class_="list-unstyled cities block-regions"):
            for region_link in ul.find_all("a"):
                region_name = region_link.find("span", class_="city-name").text.strip()
                region_href = region_link["href"]

                # Используем urljoin для безопасного формирования URL
                region_full_url = urljoin(SITE_URL, region_href)

                try:
                    region_response = session.get(region_full_url, timeout=10)
                    region_response.raise_for_status()
                except requests.RequestException as e:
                    print(f"[WARN] Could not fetch region page for {region_name}: {e}")
                    continue

                region_soup = BeautifulSoup(region_response.text, "html.parser")
                city_blocks = region_soup.find_all("ul", class_="list-unstyled cities")
                time.sleep(1.5)

                if not city_blocks:
                    cities[region_name] = region_href
                    print(f"[INFO] Parsed region: {region_name} -> {region_href}")
                else:
                    for city_link in city_blocks[0].find_all("a"):
                        city_name = city_link.find(
                            "span", class_="city-name"
                        ).text.strip()
                        city_href = city_link["href"]
                        cities[city_name] = city_href
                        print(f"[INFO] Parsed city: {city_name} -> {city_href}")

        print(f"[SUCCESS] Found {len(cities)} cities in total.")
        return cities

    def __check_and_find_unique_stop(self, name, coord, node_map):
        """Проверяет уникальность остановки и при необходимости добавляет суффикс."""
        is_new = True
        original_name = name
        suffix = 1
        while name in node_map:
            old = node_map[name]
            old_coord = Coordinate(old["xCoordinate"], old["yCoordinate"])
            if self.are_stops_same(old_coord, coord):
                is_new = False
                break
            # Логика инкремента вынесена из increment_suffix для большей надежности
            name = f"{original_name} {suffix}"
            suffix += 1
        return name, is_new

    # === Site Parsing Logic ===
    def get_all_routes_info(self):
        """Возвращает список маршрутов: номер, имя и URL."""
        full_url = urljoin(SITE_URL, self.city_url + self.transport_url)
        try:
            response = session.get(full_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to get routes list from {full_url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("a", class_=self.transport_class)
        return [[i.text.strip(), i.find("span").text.strip(), i["href"]] for i in items]

    def get_timetable(self, route_url):
        """Получает расписание для маршрута в обоих направлениях."""
        def parse_dir(suffix):
            """Парсит расписание для указанного направления (A/B)."""
            full_url = urljoin(SITE_URL, route_url + suffix)
            try:
                resp = session.get(full_url, timeout=10)
                resp.raise_for_status()
            except requests.RequestException:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")
            stops = []
            for s in soup.find_all("div", class_="bus-stop"):
                name_tag = s.find("a")
                next_div = s.find_next_sibling("div", class_="col-xs-12")
                time_tag = next_div.find("span") if next_div else None
                if not name_tag or not time_tag:
                    continue
                name = re.sub(r"\d+\) ", "", name_tag.text.strip())
                stops.append(
                    {"stopName": name, "timePoint": time_tag.text.strip().rstrip("K")}
                )
            return stops

        t1 = parse_dir(TIMETABLE_FORWARD_URL)
        t2 = parse_dir(TIMETABLE_BACKWARD_URL)

        if t1 is None and t2 is None:
            return None, False

        combined = (t1 or []) + (t2 or [])
        return (combined, True) if combined else (None, False)

    def get_stop_coordinates(self, route_url):
        """Извлекает координаты остановок из страницы карты маршрута."""
        full_url = urljoin(SITE_URL, route_url + MAP_URL)
        try:
            response = session.get(full_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = next(
            (
                s
                for s in soup.find_all("script", type="text/javascript")
                if "drawMap" in s.text
            ),
            None,
        )

        if not script_tag:
            return {}

        matches = re.findall(
            r'{"name":\s*"(.*?)",\s*"lat":\s*(-?\d+\.?\d*),\s*"long":\s*(-?\d+\.?\d*)}',
            script_tag.text,
        )
        return {
            m[0].replace("\\", ""): Coordinate(float(m[2]), float(m[1]))
            for m in matches
        }

    # === Utility Methods ===
    def load_cache(self, path):
        """Загружает данные из кеша, если он актуален."""
        if self.__is_cache_fresh(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_cache(self, path, data):
        """Сохраняет словарь в кеш по указанному пути."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # === Math Helpers ===
    def calculate_duration(self, start, end):
        """Считает длительность в минутах между двумя точками времени."""
        try:
            h1, m1 = map(int, start.split(":"))
            h2, m2 = map(int, end.split(":"))

            min1 = h1 * 60 + m1
            min2 = h2 * 60 + m2

            diff = min2 - min1
            if diff < 0:
                diff += 24 * 60  # сутки в минутах

            if diff == 0:
                return False
            return diff
        except Exception:
            return False

    def are_stops_same(self, c1, c2, tol=0.005):
        """Проверяет близость координат остановок с заданной точностью."""
        if not c1.is_defined() or not c2.is_defined():
            return False
        return math.dist(c1.get_xy(), c2.get_xy()) < tol

    @abstractmethod
    def get_transport_class(self): ...
    @abstractmethod
    def get_transport_url(self): ...


# === Concrete Implementations ===
class BusGraphParser(AbstractTransportGraphParser):
    def get_transport_url(self):
        """Возвращает относительный URL раздела автобусов."""
        return "bus/"

    def get_transport_class(self):
        """CSS-класс элементов списка автобусных маршрутов."""
        return "bus-item bus-icon"


class TrolleyGraphParser(AbstractTransportGraphParser):
    def get_transport_url(self):
        """Возвращает относительный URL раздела троллейбусов."""
        return "trolley/"

    def get_transport_class(self):
        """CSS-класс элементов списка троллейбусных маршрутов."""
        return "bus-item trolley-icon"


class MiniBusGraphParser(AbstractTransportGraphParser):
    def get_transport_url(self):
        """Возвращает относительный URL раздела маршрутных такси."""
        return "mtaxi/"

    def get_transport_class(self):
        """CSS-класс элементов списка маршрутов маршрутных такси."""
        return "bus-item mtaxi-icon"


class TramGraphParser(AbstractTransportGraphParser):
    def get_transport_url(self):
        """Возвращает относительный URL раздела трамваев."""
        return "tram/"

    def get_transport_class(self):
        """CSS-класс элементов списка трамвайных маршрутов."""
        return "bus-item tram-icon"


class Coordinate:
    def __init__(self, x=None, y=None, is_approximate=False):
        """Создаёт координату с признаком приблизительности."""
        self.x = x
        self.y = y
        self.is_approximate = is_approximate

    def __str__(self):
        """Строковое представление координаты."""
        return f"Coordinate(x={self.x}, y={self.y}, approx={self.is_approximate})"

    def is_defined(self):
        """Проверяет, заданы ли обе координаты (x, y)."""
        return self.x is not None and self.y is not None

    def get_xy(self):
        """Возвращает координаты как список [x, y]."""
        return [self.x, self.y]