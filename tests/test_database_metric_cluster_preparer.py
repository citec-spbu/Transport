import pytest

import app.database.metric_cluster_preparer as db_mcp
from app.core.context.analysis_context import AnalysisContext
from app.core.context.db_graph_parameters import DBGraphParameters
from app.core.context.metric_calculation_context import MetricCalculationContext


class _StubConn:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def read_all(self, query, parameters=None):
        self.calls.append(("read_all", query))
        return self.rows


class _StubDetector:
    def __init__(self):
        self.detected = []

    def detect_communities(self, graph_name, weight):
        self.detected.append((graph_name, weight))


class _StubMetric:
    def __init__(self):
        self.calls = []

    def metric_calculate(self, graph_name, weight):
        self.calls.append((graph_name, weight))


def _ctx_with_flags(**flags):
    mc = MetricCalculationContext(**flags)
    db_params = DBGraphParameters()
    db_params.main_node_name = "Stop"
    db_params.weight = "duration"
    return AnalysisContext(
        metric_calculation_context=mc,
        graph_name="G",
        db_graph_parameters=db_params,
    )


def test_db_preparer_runs_selected_tasks(monkeypatch):
    rows = [
        {
            "id": "n1",
            "name": "Node",
            "lon": 1.0,
            "lat": 2.0,
            "leiden_community": 7,
            "louvain_community": 3,
            "betweenness": 0.4,
            "pagerank": 0.6,
        }
    ]
    stub_conn = _StubConn(rows)
    monkeypatch.setattr(db_mcp, "Neo4jConnection", lambda: stub_conn)

    stub_leiden = _StubDetector()
    stub_louvain = _StubDetector()
    stub_metric = _StubMetric()
    monkeypatch.setattr(db_mcp, "Leiden", lambda: stub_leiden)
    monkeypatch.setattr(db_mcp, "Louvain", lambda: stub_louvain)
    monkeypatch.setattr(db_mcp, "Betweenness", lambda: stub_metric)
    monkeypatch.setattr(db_mcp, "PageRank", lambda: stub_metric)

    ctx = _ctx_with_flags(
        need_leiden_clusterization=True,
        need_louvain_clusterization=True,
        need_betweenness=True,
        need_pagerank=True,
    )

    preparer = db_mcp.MetricClusterPreparer(ctx)
    nodes = preparer.prepare_metrics()

    assert stub_leiden.detected == [("G", "duration")]
    assert stub_louvain.detected == [("G", "duration")]
    assert stub_metric.calls == [("G", "duration"), ("G", "duration")]
    assert nodes == [
        {
            "id": "n1",
            "name": "Node",
            "coordinates": [1.0, 2.0],
            "cluster_id": 3,
            "metric": 0.6,
        }
    ]


def test_db_preparer_returns_nodes_without_metrics(monkeypatch):
    rows = [
        {
            "id": "n2",
            "name": "Bare",
            "lon": 0,
            "lat": 0,
            "leiden_community": None,
            "louvain_community": None,
            "betweenness": 0.0,
            "pagerank": 0.0,
        }
    ]
    stub_conn = _StubConn(rows)
    monkeypatch.setattr(db_mcp, "Neo4jConnection", lambda: stub_conn)
    monkeypatch.setattr(db_mcp, "Leiden", lambda: None)
    monkeypatch.setattr(db_mcp, "Louvain", lambda: None)
    monkeypatch.setattr(db_mcp, "Betweenness", lambda: None)
    monkeypatch.setattr(db_mcp, "PageRank", lambda: None)

    ctx = _ctx_with_flags()
    preparer = db_mcp.MetricClusterPreparer(ctx)

    nodes = preparer.prepare_metrics()
    assert nodes == [
        {
            "id": "n2",
            "name": "Bare",
            "coordinates": [0, 0],
        }
    ]
