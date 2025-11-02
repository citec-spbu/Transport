import datetime
import json
import math
import os
import re
import time
from abc import abstractmethod

import requests
from bs4 import BeautifulSoup
"""
    Класс занимающийся парсингом данных с сайта https://kudikina.ru
"""

cache_file = '../cache/city_urls.json'
cache_expire_days = 30
site_url = "https://kudikina.ru"
map_url = "/map"
timetable_forward_url = "/A"
timetable_backward_url = "/B"
city_avg_x_coordinate = 30.3351 
city_avg_y_coordinate = 59.9343
request_pause_sec = 2


class AbstractTransportGraphParser:

    def __init__(self, city_name):
        self.city_name = city_name
        self.city_url = self.__get_city_url()
        self.nodes = {}
        self.relationships = []
        self.transport_url = self.get_transport_url()
        self.transport_class = self.get_transport_class()

    def parse(self):
        if self.city_url is None:
            return None, None

        for route_info in self.get_all_routes_info():
            route_name = route_info[0]
            route_url = route_info[2]

            self.__add_stops_and_routes(route_name, route_url)

            print(route_url)
            time.sleep(request_pause_sec)

        return self.nodes, self.relationships

    def __get_city_url(self):
        cities_url = self.load_cache(cache_file)
        if not cities_url:
            print("Cities url cache is expired or empty, lets fill it.")
            cities_url = self.parse_all_city_urls()
            self.save_cache(cache_file, cities_url)
            print("Cities url are saved in cache.")
        city_url = cities_url.get(self.city_name)
        if city_url is None:
            print('No such city in parsed data')
        return city_url

    def __add_stops_and_routes(self, route_name, route_url):
        (timetable, successes_parse) = self.get_timetable(route_url)
        if successes_parse is False:
            return

        stop_coordinates = self.get_stop_coordinates(route_url)
        last_coordinate = Coordinate(city_avg_x_coordinate, city_avg_y_coordinate)
        previous_transport_stop_name = None
        previous_time_point = None

        for row in timetable:
            transport_stop_name = row["stopName"]
            time_point = row["timePoint"]
            coordinate = self.__get_filled_coordinate(stop_coordinates, transport_stop_name, last_coordinate)

            transport_stop = self.__update_or_add_stop(transport_stop_name, coordinate, route_name)

            if previous_transport_stop_name is not None:
                duration = self.calculate_duration(previous_time_point, time_point)
                if duration is False:
                    continue
                self.__add_route(
                    previous_transport_stop_name,
                    transport_stop,
                    duration,
                    route_name
                )

            last_coordinate = coordinate
            previous_transport_stop_name = transport_stop
            previous_time_point = time_point

    def __get_filled_coordinate(self, stop_coordinates, stop_name, last_coordinate):
        coordinate = stop_coordinates.get(stop_name)
        if coordinate is None or not coordinate.is_defined():
            coordinate = Coordinate(last_coordinate.x, last_coordinate.y, True)
        return coordinate

    def __update_or_add_stop(self, transport_stop_name, coordinate, route_name):

        transport_stop_name, is_new_stop = self.__check_and_find_unique_stop(transport_stop_name, coordinate)

        if not is_new_stop:
            transport_stop = self.nodes.get(transport_stop_name)
            transport_stop["roteList"].append(route_name)
        else:
            transport_stop = {
                "name": transport_stop_name,
                "roteList": [route_name],
                "xCoordinate": coordinate.x,
                "yCoordinate": coordinate.y,
                "isCoordinateApproximate": coordinate.is_approximate
            }
            self.nodes[transport_stop_name] = transport_stop
        return transport_stop

    def __check_and_find_unique_stop(self, transport_stop_name, coordinate):
        is_new_stop = True
        while self.nodes.get(transport_stop_name) is not None:
            transport_stop = self.nodes[transport_stop_name]
            old_coordinate = Coordinate(transport_stop["xCoordinate"], transport_stop["yCoordinate"])
            if self.are_stops_same(old_coordinate, coordinate):
                is_new_stop = False
                break
            else:
                transport_stop_name = self.increment_suffix(transport_stop_name)

        return transport_stop_name, is_new_stop

    def __add_route(self, start_stop, end_stop, duration, route_name):
        if start_stop is not None and end_stop is not None:
            self.relationships.append({"startStop": start_stop["name"],
                                       "endStop": end_stop["name"],
                                       "name": start_stop["name"] + " -> " + end_stop[
                                           "name"] + "; route_name: " + route_name,
                                       "route": route_name,
                                       "duration": duration
                                       })

    def get_all_routes_info(self):
        if self.city_url is None:
            return []

        full_url = site_url + self.city_url + self.transport_url

        response = requests.get(full_url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        transport_list = []

        bus_items = soup.find_all("a", class_=self.transport_class)
        for item in bus_items:
            transport_number = item.text.strip()
            transport_route = item.find("span").text.strip()
            href_link = item["href"]
            transport_list.append([transport_number, transport_route, href_link])
        return transport_list

    def get_timetable(self, route_url):
        (timetable1, successes_parse1) = self.get_one_direction_timetable(route_url, timetable_forward_url)
        (timetable2, successes_parse2) = self.get_one_direction_timetable(route_url, timetable_backward_url)
        if successes_parse1 and successes_parse2:
            return timetable1 + timetable2, True
        else:
            return None, False

    def get_one_direction_timetable(self, route_url, timetable_url):
        full_url = site_url + route_url + timetable_url

        response = requests.get(full_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        stop_times = []
        for stop_div in soup.find_all('div', class_='bus-stop'):
            name = stop_div.find('a').text.strip()
            time_point = stop_div.find_next_sibling('div', class_='col-xs-12').find('span')
            if time_point is not None:
                parsed_time_point = time_point.text.strip()
                if parsed_time_point[len(parsed_time_point) - 1] == 'K':
                    parsed_time_point = parsed_time_point[:-1]
            else:
                return None, False
            clean_name = re.sub(r"\d+\) ", "", name)
            stop_times.append({"stopName": clean_name, "timePoint": parsed_time_point})
        return stop_times, True

    def get_stop_coordinates(self, route_url):
        full_url = site_url + route_url + map_url
        response = requests.get(full_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        script_tags = soup.find_all('script', type="text/javascript")
        script_tag = None

        for tag in script_tags:
            if 'drawMap' in tag.text:
                script_tag = tag
                break

        if script_tag:
            script_text = script_tag.text
            coordinates = self.extract_coordinates(script_text)

            return coordinates
        else:
            return {}

    def extract_coordinates(self, script_text):
        matches = re.findall(r'{"name":\s*"(.*?)",\s*"lat":\s*(-?\d+\.?\d*),?\s*"long":\s*(-?\d+\.?\d*)?}', script_text)

        coordinates = {}
        for match in matches:
            name = match[0].replace("\\", "")
            # `match` contains latitude and longitude which equals to y and x coordinates
            x = float(match[2])
            y = float(match[1])
            coordinates[name] = Coordinate(x, y)

        return coordinates

    def load_cache(self, cache_file):
        if os.path.exists(cache_file):
            modification_time = os.path.getmtime(cache_file)
            current_time = datetime.datetime.now()
            if (current_time - datetime.datetime.fromtimestamp(modification_time)).days <= cache_expire_days:
                with open(cache_file, 'r') as file:
                    return json.load(file)
        return {}

    def save_cache(self, cache_file, cache_data):
        cache_dir = os.path.dirname(cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        with open(cache_file, 'w') as file:
                json.dump(cache_data, file)

    def parse_all_city_urls(self):
        url = "https://kudikina.ru/"
        response = requests.get(url)
        time.sleep(2)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        cities = {}

        for li in soup.find_all('ul', class_='list-unstyled cities block-regions'):
            for region in li.find_all('a'):
                region_name = region.find('span', class_='city-name').text.strip()
                region_href = region['href']
                region_response = requests.get(url[:-1] + region_href)
                region_html_content = region_response.text
                region_soup = BeautifulSoup(region_html_content, 'html.parser')
                city_list = region_soup.find_all('ul', class_='list-unstyled cities')
                time.sleep(2)
                if len(city_list) == 0:
                    cities[region_name] = region_href
                    print(region_href + ' Was parsed')
                else:
                    region_cities = city_list[0].find_all('a')
                    for city in region_cities:
                        city_name = city.find('span', class_='city-name').text.strip()
                        city_href = city['href']
                        cities[city_name] = city_href
                        print(city_href + ' Was parsed')
        return cities

    def calculate_duration(self, start_stop, end_stop):
        try:
            start_hour, start_minute = map(int, start_stop.split(':'))
            end_hour, end_minute = map(int, end_stop.split(':'))
            return abs((end_hour * 60 + end_minute) - (start_hour * 60 + start_minute))
        except ValueError:
            return False
        except AttributeError:
            return False
    def are_stops_same(self, coord1, coord2, tolerance=0.005):
        distance = math.dist(coord1.get_xy(), coord2.get_xy())
        return abs(distance) < tolerance

    def increment_suffix(self, name):
        if name and name[-1].isdigit():
            index = len(name) - 1
            while index >= 0 and name[index].isdigit():
                index -= 1
            number = int(name[index + 1:]) + 1
            return f"{name[:index + 1]}{number}"
        else:
            return f"{name} 1"

    @abstractmethod
    def get_transport_class(self):
        pass

    @abstractmethod
    def get_transport_url(self):
        pass


class BusGraphParser(AbstractTransportGraphParser):
    def get_transport_class(self):
        return "bus-item bus-icon"

    def get_transport_url(self):
        return "bus/"


class TrolleyGraphParser(AbstractTransportGraphParser):
    def get_transport_url(self):
        return "trolley/"

    def get_transport_class(self):
        return "bus-item trolley-icon"


class BusGraphParser(AbstractTransportGraphParser):

    def get_transport_url(self):
        return "bus/"

    def get_transport_class(self):
        return "bus-item bus-icon"


class MiniBusGraphParser(AbstractTransportGraphParser):
    def get_transport_url(self):
        return "mtaxi/"

    def get_transport_class(self):
        return "bus-item mtaxi-icon"


class TramGraphParser(AbstractTransportGraphParser):
    def get_transport_url(self):
        return "tram/"

    def get_transport_class(self):
        return "bus-item tram-icon"


class Coordinate:
    def __init__(self, x=None, y=None, is_approximate=False):
        self.x = x
        self.y = y
        self.is_approximate = is_approximate

    def __str__(self):
        return f"({self.x}, {self.y})"

    def is_defined(self):
        if self.x is None or self.y is None:
            return False
        else:
            return True

    def get_xy(self):
        return [self.x, self.y]
