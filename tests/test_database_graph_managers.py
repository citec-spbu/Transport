from types import SimpleNamespace

import pandas as pd
import pytest

import app.database.graph_db_manager as gdm
import app.database.transport_db_manager as tdm
from app.core.context.analysis_context import AnalysisContext
from app.core.context.db_graph_parameters import DBGraphParameters
from app.core.context.metric_calculation_context import MetricCalculationContext


class _FakeTx:
    def __init__(self):
        self.queries = []

    def run(self, query, parameters=None):
        self.queries.append((query, parameters))
        count = len(parameters.get("rows", [])) if parameters else 0
        # Mimic neo4j result object with data() method
        return SimpleNamespace(data=lambda: [{"total": count}])


class _StubConn:
    def __init__(self):
        self.exec_calls = []
        self.read_calls = []

    def execute_write(self, func, *args, **kwargs):
        self.exec_calls.append((func.__name__, args, kwargs))
        tx = _FakeTx()
        return func(tx, *args, **kwargs)

    def read_all(self, query, parameters=None):
        self.read_calls.append((query, parameters))
        return ["ok"]


class _DummyManager(gdm.OneTypeNodeDBManager):
    def __init__(self, ctx, graph):
        self._graph = graph
        super().__init__(ctx)

    def get_graph(self):
        return self._graph

    def get_weight(self):
        return "duration"

    def node_geometry_identity(self):
        return "location"

    def get_bd_all_node_query_graph(self):
        return "MATCH (n) RETURN n"

    def get_bd_all_rels_query_graph(self):
        return "MATCH ()-[r]->() RETURN r"

    def get_node_name(self):
        return "123 Bad/Node"

    def get_rels_name(self):
        return "456 Bad/Rel"

    def get_constraint_list(self):
        return ["CREATE CONSTRAINT demo"]

    def create_node_query(self):
        return "UNWIND $rows AS row RETURN 1"

    def create_relationships_query(self):
        return "UNWIND $rows AS rel RETURN 1"


@pytest.fixture(autouse=True)
def _patch_conn(monkeypatch):
    # Patch once on the module that actually instantiates the connection
    monkeypatch.setattr(gdm, "Neo4jConnection", lambda: _StubConn())


def _base_context(city="City"):
    mc = MetricCalculationContext()
    db_params = DBGraphParameters()
    return AnalysisContext(metric_calculation_context=mc, city_name=city, db_graph_parameters=db_params)


def test_update_db_ignores_empty_graph():
    ctx = _base_context()
    manager = _DummyManager(ctx, graph=(None, None))
    manager.connection.exec_calls.clear()

    manager.update_db("City")
    assert manager.connection.exec_calls == []


def test_update_db_writes_batches(monkeypatch):
    nodes = [{"name": "A"}, {"name": "B"}]
    rels = [
        {"startStop": "A", "endStop": "B", "name": "A-B", "route": "1", "duration": 5},
    ]
    ctx = _base_context()
    manager = _DummyManager(ctx, graph=(nodes, rels))

    manager.update_db("City")

    # Should execute constraints + two insert_data calls
    exec_names = [c[0] for c in manager.connection.exec_calls]
    assert exec_names == ["create_constraints", "insert_data", "insert_data"]


def test_safe_names_are_generated():
    ctx = _base_context()
    manager = _DummyManager(ctx, graph=([], []))
    assert manager.db_graph_parameters.main_node_name == "_123BadNode"
    assert manager.db_graph_parameters.main_rels_name == "_456BadRel"


class _StubParser:
    def __init__(self, city):
        self.city = city
        self.parse_called = False

    def parse(self):
        self.parse_called = True
        nodes = {"S1": {"name": "S1", "routeList": ["1"], "xCoordinate": 1, "yCoordinate": 2, "isCoordinateApproximate": False}}
        rels = [{"startStop": "S1", "endStop": "S1", "name": "loop", "route": "1", "duration": 10}]
        return nodes, rels


def test_transport_manager_get_graph_and_update(monkeypatch):
    monkeypatch.setattr(tdm, "BusGraphParser", lambda city: _StubParser(city))
    ctx = _base_context(city="DemoCity")
    manager = tdm.BusGraphDBManager(ctx)

    nodes, rels = manager.get_graph()
    assert nodes and rels

    manager.update_db("DemoCity")
    exec_names = [c[0] for c in manager.connection.exec_calls]
    assert exec_names == ["create_constraints", "insert_data", "insert_data"]


def test_transport_manager_queries_and_constraints(monkeypatch):
    # Use stub parser to avoid network
    monkeypatch.setattr(tdm, "BusGraphParser", lambda city: _StubParser(city))
    manager = tdm.BusGraphDBManager(_base_context(city="Q"))

    # Ensure Cypher templates render with sanitized labels
    assert "QBusStop" in manager.create_node_query()
    assert "QBusRouteSegment" in manager.create_relationships_query()

    # Constraint list present
    constraints = manager.get_constraint_list()
    assert any("QBusStop" in c for c in constraints)
    assert any("QBusRouteSegment" in c for c in constraints)

    # get_bd_all_* queries are constructed
    manager.get_bd_all_node_query_graph()
    manager.get_bd_all_rels_query_graph()


def test_enrich_db_parameters_and_queries(monkeypatch):
    ctx = _base_context(city="MegaCity")
    manager = _DummyManager(ctx, graph=([], []))

    # get_bd_all_node_graph/get_bd_all_rels_graph should call read_all with built queries
    manager.get_bd_all_node_graph()
    manager.get_bd_all_rels_graph()
    assert len(manager.connection.read_calls) == 2

    # create_constraints should run provided constraints
    tx = _FakeTx()
    manager.create_constraints(tx)
    assert tx.queries == [("CREATE CONSTRAINT demo", None)]


def test_insert_data_batches_and_counts():
    tx = _FakeTx()
    rows = [{"name": "X"}, {"name": "Y"}, {"name": "Z"}]
    total = gdm.insert_data(tx, "UNWIND $rows AS row RETURN 1", rows, batch_size=2)
    assert total == 3
    assert len(tx.queries) == 2


def test_transport_specific_names_and_weight(monkeypatch):
    monkeypatch.setattr(tdm, "BusGraphParser", lambda city: _StubParser(city))
    monkeypatch.setattr(tdm, "TrolleyGraphParser", lambda city: _StubParser(city))
    monkeypatch.setattr(tdm, "TramGraphParser", lambda city: _StubParser(city))
    monkeypatch.setattr(tdm, "MiniBusGraphParser", lambda city: _StubParser(city))

    ctx = _base_context(city="CityX")
    bus = tdm.BusGraphDBManager(ctx)
    assert bus.get_node_name() == "CityXBusStop"
    assert bus.get_rels_name() == "CityXBusRouteSegment"
    assert bus.get_weight() == "duration"

    trolley = tdm.TrolleyGraphDBManager(ctx)
    assert trolley.get_node_name() == "CityXTrolleyStop"
    assert trolley.get_rels_name() == "CityXTrolleyRouteSegment"

    tram = tdm.TramGraphDBManager(ctx)
    assert tram.get_node_name() == "CityXTramStop"
    assert tram.get_rels_name() == "CityXTramRouteSegment"

    mini = tdm.MiniBusGraphDBManager(ctx)
    assert mini.get_node_name() == "CityXMiniBusStop"
    assert mini.get_rels_name() == "CityXMiniBusRouteSegment"
