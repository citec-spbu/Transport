import json
import os
import time

import pytest

import app.core.services.parsers as parsers


class DummyParser(parsers.AbstractTransportGraphParser):
    def get_transport_url(self):
        return "bus/"

    def get_transport_class(self):
        return "bus-item"


class _Resp:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise parsers.requests.RequestException("boom")


@pytest.fixture
def parser(tmp_path, monkeypatch):
    # Avoid hitting network for city URLs and cache paths
    monkeypatch.setattr(parsers.AbstractTransportGraphParser, "_AbstractTransportGraphParser__get_city_url", lambda self: "/dummy")
    monkeypatch.setattr(parsers, "BASE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(parsers, "CITY_CACHE_DIR", str(tmp_path / "cache" / "cities"))
    return DummyParser("Demo")


def test_get_route_path_sanitizes(parser):
    path = parser._AbstractTransportGraphParser__get_route_path("Маршрут 1/2")
    assert os.path.basename(path) == "Маршрут_1_2.json"


def test_is_cache_fresh(tmp_path, parser):
    p = tmp_path / "file.json"
    p.write_text("{}", encoding="utf-8")
    assert parser._AbstractTransportGraphParser__is_cache_fresh(str(p)) is True

    old = time.time() - (parsers.CACHE_EXPIRE_DAYS + 2) * 24 * 3600
    os.utime(p, (old, old))
    assert parser._AbstractTransportGraphParser__is_cache_fresh(str(p)) is False


def test_merge_route_data_combines_and_filters(parser):
    data = {
        "nodes": {
            "Stop": {"routeList": ["1"], "xCoordinate": 1, "yCoordinate": 2, "isCoordinateApproximate": False},
            "Stop2": {"routeList": ["2"], "xCoordinate": 3, "yCoordinate": 4, "isCoordinateApproximate": False},
        },
        "relationships": [
            {"duration": 5},
            {"duration": 0},  # filtered out
            {"duration": None},  # filtered out
        ],
    }

    parser._AbstractTransportGraphParser__merge_route_data(data)

    assert parser.nodes["Stop"]["routeList"] == ["1"]
    assert parser.nodes["Stop2"]["routeList"] == ["2"]
    assert len(parser.relationships) == 1


def test_check_and_find_unique_stop(parser):
    c1 = parsers.Coordinate(1, 1)
    c2 = parsers.Coordinate(1.0001, 1.0001)
    name, is_new = parser._AbstractTransportGraphParser__check_and_find_unique_stop("A", c1, {"A": {"xCoordinate": 1, "yCoordinate": 1}})
    assert is_new is False
    assert name == "A"

    name2, is_new2 = parser._AbstractTransportGraphParser__check_and_find_unique_stop("A", c2, {"A": {"xCoordinate": 2, "yCoordinate": 2}})
    assert is_new2 is True
    assert name2.startswith("A ")


def test_calculate_duration_and_wrap(parser):
    assert parser.calculate_duration("10:00", "10:30") == 30
    assert parser.calculate_duration("23:50", "00:10") == 20
    assert parser.calculate_duration("10:00", "10:00") is False
    assert parser.calculate_duration("bad", "00:00") is False


def test_are_stops_same(parser):
    c1 = parsers.Coordinate(1, 1)
    c2 = parsers.Coordinate(1.0001, 1.0002)
    assert parser.are_stops_same(c1, c2, tol=0.01) is True
    assert parser.are_stops_same(parsers.Coordinate(None, 1), c2) is False


def test_load_and_save_cache(tmp_path, parser):
    path = tmp_path / "cache.json"
    parser.save_cache(str(path), {"a": 1})
    assert parser.load_cache(str(path)) == {"a": 1}


def test_get_stop_coordinates_parses_script(monkeypatch, parser):
    script = '<script type="text/javascript">drawMap([{"name":"Stop \\\"1\\\"","lat":55.1,"long":37.6}])</script>'
    html = f"<html><body>{script}</body></html>"
    monkeypatch.setattr(parsers.session, "get", lambda url, timeout=10: _Resp(html))

    coords = parser.get_stop_coordinates("/route")
    coord = coords['Stop "1"']
    assert isinstance(coord, parsers.Coordinate)
    assert coord.x == 37.6
    assert coord.y == 55.1


def test_get_timetable_parses(monkeypatch, parser):
    html = '''
    <div class="bus-stop"><a>1) Main</a></div>
    <div class="col-xs-12"><span>12:00K</span></div>
    '''
    monkeypatch.setattr(parsers.session, "get", lambda url, timeout=10: _Resp(html))

    timetable, ok = parser.get_timetable("/route")
    assert ok is True
    assert len(timetable) == 2  # forward + backward
    assert timetable[0]["stopName"] == "Main"
    assert timetable[0]["timePoint"] == "12:00"


def test_get_all_routes_info_parses(monkeypatch, parser):
    html = '<a class="bus-item" href="/route1">1<span>Route Name</span></a>'
    monkeypatch.setattr(parsers.session, "get", lambda url, timeout=10: _Resp(html))

    routes = parser.get_all_routes_info()
    assert len(routes) == 1
    assert routes[0][2] == "/route1"  # href is correct
    assert "Route Name" in routes[0][1]  # span text present


def test_parse_all_city_urls(monkeypatch):
    main_html = '<ul class="list-unstyled cities block-regions"><a href="/r"><span class="city-name">Region</span></a></ul>'
    region_html = '<ul class="list-unstyled cities"><a href="/c"><span class="city-name">CityA</span></a></ul>'

    def fake_get(url, timeout=15):
        if url.endswith("/r"):
            return _Resp(region_html)
        return _Resp(main_html)

    monkeypatch.setattr(parsers.session, "get", fake_get)
    parser = DummyParser("Demo")
    cities = parser.parse_all_city_urls()
    assert cities == {"CityA": "/c"}


def test_parse_uses_cached_routes(monkeypatch, tmp_path):
    monkeypatch.setattr(parsers, "BASE_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(parsers, "CITY_CACHE_DIR", str(tmp_path / "cache" / "cities"))
    
    # Prevent network call by patching __get_city_url before creating parser
    def fake_get_city_url(self):
        return "/dummy"
    monkeypatch.setattr(parsers.AbstractTransportGraphParser, "_AbstractTransportGraphParser__get_city_url", fake_get_city_url)

    parser = DummyParser("Demo")
    routes_index = parser.city_dir + "/routes_index.json"
    os.makedirs(parser.city_dir, exist_ok=True)
    with open(routes_index, "w", encoding="utf-8") as f:
        json.dump([["R1", "Route One", "/r1"]], f)

    route_path = parser._AbstractTransportGraphParser__get_route_path("R1")
    with open(route_path, "w", encoding="utf-8") as f:
        json.dump({
            "nodes": {
                "S": {"name": "S", "routeList": ["R1"], "xCoordinate": 1, "yCoordinate": 2, "isCoordinateApproximate": False}
            },
            "relationships": [{"startStop": "S", "endStop": "S", "name": "loop", "route": "R1", "duration": 10}],
            "timestamp": "now"
        }, f)

    monkeypatch.setattr(parser, "_AbstractTransportGraphParser__is_cache_fresh", lambda path: True)
    monkeypatch.setattr(parser, "_AbstractTransportGraphParser__parse_single_route", lambda *a, **kw: None)
    monkeypatch.setattr(time, "sleep", lambda *a, **kw: None)

    nodes, rels = parser.parse(use_cache=True)
    assert nodes is not None and rels is not None
    assert "S" in nodes
    assert rels[0]["duration"] == 10