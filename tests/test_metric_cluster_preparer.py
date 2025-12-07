import pytest

from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.metric_cluster.metric_cluster_preparer import MetricClusterPreparer
from app.database import neo4j_connection


def _patch_and_run(monkeypatch, rows, mc):
    """Patch Neo4j read_all and run _load_nodes_with_metrics()."""
    def fake_read_all(self, query, parameters=None):
        # Basic query validation
        assert "location.longitude" in query
        assert "location.latitude" in query
        return rows

    monkeypatch.setattr(
        neo4j_connection.Neo4jConnection,
        "read_all",
        fake_read_all,
    )

    ctx = AnalysisContext(metric_calculation_context=mc)
    ctx.db_graph_parameters.main_node_name = "TestNode"

    preparer = MetricClusterPreparer(ctx)
    return preparer._load_nodes_with_metrics()


def _assert_base_node(node, expected_id, expected_name, lon, lat, expected_metric=None, expected_cluster=None):
    """
    Shared assertions for node structure and optionally metric/cluster values.
    """
    assert node["id"] == expected_id
    assert node["name"] == expected_name
    assert node["coordinates"] == [lon, lat]

    if expected_metric is not None:
        assert "metric" in node
        assert node["metric"] == expected_metric
    else:
        assert "metric" not in node

    if expected_cluster is not None:
        assert "cluster_id" in node
        assert node["cluster_id"] == expected_cluster
    else:
        assert "cluster_id" not in node


def test_load_nodes_without_flags(monkeypatch):
    rows = [
        {
            "id": "100",
            "name": "StopA",
            "lon": 30.123,
            "lat": 59.987,
            "leiden_community": 1,
            "louvain_community": None,
            "betweenness": None,
            "pagerank": 0.123,
        }
    ]

    mc = MetricCalculationContext()
    nodes = _patch_and_run(monkeypatch, rows, mc)

    assert len(nodes) == 1
    _assert_base_node(nodes[0], "100", "StopA", 30.123, 59.987)


def test_load_nodes_with_pagerank_flag(monkeypatch):
    rows = [
        {
            "id": "200",
            "name": "StopB",
            "lon": 31.0,
            "lat": 60.0,
            "leiden_community": None,
            "louvain_community": None,
            "betweenness": None,
            "pagerank": 0.456,
        }
    ]

    mc = MetricCalculationContext()
    mc.need_pagerank = True

    nodes = _patch_and_run(monkeypatch, rows, mc)

    assert len(nodes) == 1
    _assert_base_node(nodes[0], "200", "StopB", 31.0, 60.0, expected_metric=0.456)


def test_load_nodes_with_betweenness_flag(monkeypatch):
    rows = [
        {
            "id": "300",
            "name": "StopC",
            "lon": 32.0,
            "lat": 61.0,
            "leiden_community": None,
            "louvain_community": None,
            "betweenness": 2.5,
            "pagerank": None,
        }
    ]

    mc = MetricCalculationContext()
    mc.need_betweenness = True

    nodes = _patch_and_run(monkeypatch, rows, mc)

    assert len(nodes) == 1
    _assert_base_node(nodes[0], "300", "StopC", 32.0, 61.0, expected_metric=2.5)


def test_load_nodes_with_leiden_flag(monkeypatch):
    rows = [
        {
            "id": "400",
            "name": "StopD",
            "lon": 33.0,
            "lat": 62.0,
            "leiden_community": 7,
            "louvain_community": None,
            "betweenness": None,
            "pagerank": None,
        }
    ]

    mc = MetricCalculationContext()
    mc.need_leiden_clusterization = True

    nodes = _patch_and_run(monkeypatch, rows, mc)

    assert len(nodes) == 1
    _assert_base_node(nodes[0], "400", "StopD", 33.0, 62.0, expected_cluster=7)


def test_load_nodes_with_louvain_flag(monkeypatch):
    rows = [
        {
            "id": "500",
            "name": "StopE",
            "lon": 34.0,
            "lat": 63.0,
            "leiden_community": None,
            "louvain_community": 9,
            "betweenness": None,
            "pagerank": None,
        }
    ]

    mc = MetricCalculationContext()
    mc.need_louvain_clusterization = True

    nodes = _patch_and_run(monkeypatch, rows, mc)

    assert len(nodes) == 1
    _assert_base_node(nodes[0], "500", "StopE", 34.0, 63.0, expected_cluster=9)
