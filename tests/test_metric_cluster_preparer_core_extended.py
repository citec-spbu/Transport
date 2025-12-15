import pytest

import app.core.metric_cluster.metric_cluster_preparer as mcp_module
from app.core.context.analysis_context import AnalysisContext
from app.core.context.db_graph_parameters import DBGraphParameters
from app.core.context.metric_calculation_context import MetricCalculationContext


def _make_ctx(mc: MetricCalculationContext) -> AnalysisContext:
    db_params = DBGraphParameters()
    db_params.main_node_name = "Stop"
    db_params.weight = "duration"
    return AnalysisContext(
        metric_calculation_context=mc,
        graph_name="TestGraph",
        db_graph_parameters=db_params,
    )


class _StubConn:
    def __init__(self, rows):
        self.rows = rows
        self.read_queries = []

    def read_all(self, query, parameters=None):
        self.read_queries.append(query)
        return self.rows


class _StubDetector:
    def __init__(self):
        self.graph_name = None
        self.detect_called = False

    def detect_communities(self, graph_name, weight):
        self.detect_called = True
        self.graph_name = graph_name

    def calculate_modularity(self):
        return 0.11

    def calculate_conductance(self):
        return 0.22

    def calculate_coverage(self):
        return 0.33


class _StubDetectorFail(_StubDetector):
    def calculate_modularity(self):
        raise RuntimeError("modularity exploded")


class _StubMetric:
    def __init__(self):
        self.calls = []

    def metric_calculate(self, graph_name, weight):
        self.calls.append((graph_name, weight))


@pytest.fixture(autouse=True)
def _patch_neo4j(monkeypatch):
    # Prevent real Neo4j connections.
    monkeypatch.setattr(mcp_module, "Neo4jConnection", lambda: _StubConn([]))


def test_prepare_metrics_runs_all_and_returns_stats(monkeypatch):
    rows = [
        {
            "id": "1",
            "name": "A",
            "lon": 10.0,
            "lat": 20.0,
            "leiden_community": 5,
            "louvain_community": None,
            "betweenness": 0.5,
            "pagerank": 0.9,
        }
    ]
    stub_conn = _StubConn(rows)
    monkeypatch.setattr(mcp_module, "Neo4jConnection", lambda: stub_conn)

    stub_detector = _StubDetector()
    stub_metric = _StubMetric()

    monkeypatch.setattr(mcp_module, "Leiden", lambda: stub_detector)
    monkeypatch.setattr(mcp_module, "Louvain", lambda: None)
    monkeypatch.setattr(mcp_module, "Betweenness", lambda: stub_metric)
    monkeypatch.setattr(mcp_module, "PageRank", lambda: stub_metric)

    mc = MetricCalculationContext(
        need_leiden_clusterization=True,
        need_louvain_clusterization=False,
        need_betweenness=True,
        need_pagerank=True,
    )
    ctx = _make_ctx(mc)
    preparer = mcp_module.MetricClusterPreparer(ctx)

    result = preparer.prepare_metrics()

    assert stub_detector.detect_called is True
    assert stub_detector.graph_name == "TestGraph"
    assert stub_metric.calls == [("TestGraph", "duration"), ("TestGraph", "duration")]
    assert result["nodes"] == [
        {
            "id": "1",
            "name": "A",
            "coordinates": [10.0, 20.0],
            "cluster_id": 5,
            "metric": 0.9,
        }
    ]
    assert result["statistics"] == {
        "modularity": 0.11,
        "conductance": 0.22,
        "coverage": 0.33,
    }


def test_calculate_cluster_statistics_requires_detector():
    mc = MetricCalculationContext(
        need_leiden_clusterization=False,
        need_louvain_clusterization=False,
    )
    ctx = _make_ctx(mc)
    preparer = mcp_module.MetricClusterPreparer(ctx)

    with pytest.raises(ValueError, match="Cluster detector is not initialized"):
        preparer._calculate_cluster_statistics()


def test_calculate_cluster_statistics_logs_and_reraises(monkeypatch, caplog):
    stub_conn = _StubConn([])
    monkeypatch.setattr(mcp_module, "Neo4jConnection", lambda: stub_conn)

    failing_detector = _StubDetectorFail()
    monkeypatch.setattr(mcp_module, "Leiden", lambda: failing_detector)
    monkeypatch.setattr(mcp_module, "Louvain", lambda: None)
    mc = MetricCalculationContext(need_leiden_clusterization=True)
    ctx = _make_ctx(mc)

    preparer = mcp_module.MetricClusterPreparer(ctx)
    with pytest.raises(RuntimeError, match="modularity exploded"):
        with caplog.at_level("ERROR"):
            preparer._calculate_cluster_statistics()

    assert any("Error calculating cluster statistics" in m for m in caplog.messages)


def test_load_nodes_skips_incomplete_rows(monkeypatch):
    rows = [
        {
            "id": "1",
            "name": "A",
            "lon": 1,
            "lat": 2,
            "leiden_community": None,
            "louvain_community": None,
            "betweenness": None,
            "pagerank": None,
        }
    ]
    stub_conn = _StubConn(rows)
    monkeypatch.setattr(mcp_module, "Neo4jConnection", lambda: stub_conn)

    monkeypatch.setattr(mcp_module, "Leiden", lambda: _StubDetector())
    mc = MetricCalculationContext(
        need_leiden_clusterization=True,
        need_louvain_clusterization=False,
        need_betweenness=True,
        need_pagerank=True,
    )
    ctx = _make_ctx(mc)

    preparer = mcp_module.MetricClusterPreparer(ctx)
    nodes = preparer._load_nodes_with_metrics()

    assert nodes == []


def test_prepare_metrics_louvain_only(monkeypatch):
    rows = [
        {
            "id": "1",
            "name": "A",
            "lon": 1,
            "lat": 2,
            "leiden_community": None,
            "louvain_community": 9,
            "betweenness": None,
            "pagerank": 0.2,
        }
    ]
    stub_conn = _StubConn(rows)
    monkeypatch.setattr(mcp_module, "Neo4jConnection", lambda: stub_conn)

    class _LouvainStub(_StubDetector):
        pass

    louvain_stub = _LouvainStub()
    monkeypatch.setattr(mcp_module, "Leiden", lambda: None)
    monkeypatch.setattr(mcp_module, "Louvain", lambda: louvain_stub)
    monkeypatch.setattr(mcp_module, "Betweenness", lambda: None)
    monkeypatch.setattr(mcp_module, "PageRank", lambda: None)

    mc = MetricCalculationContext(
        need_leiden_clusterization=False,
        need_louvain_clusterization=True,
        need_betweenness=False,
        need_pagerank=False,
    )
    ctx = _make_ctx(mc)

    preparer = mcp_module.MetricClusterPreparer(ctx)
    result = preparer.prepare_metrics()

    assert louvain_stub.detect_called is True
    assert result["nodes"] == [
        {
            "id": "1",
            "name": "A",
            "coordinates": [1, 2],
            "cluster_id": 9,
        }
    ]
    assert result["statistics"] == {
        "modularity": 0.11,
        "conductance": 0.22,
        "coverage": 0.33,
    }
