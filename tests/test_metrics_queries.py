import re
import pytest
from app.database import neo4j_connection
from app.core.metric_cluster.community_detection import Leiden, Louvain
from app.core.metric_cluster.metrics_calculate import PageRank, Betweenness


@pytest.mark.parametrize("ClusterClass,graph_name,expected_call,expected_writeprop", [
    (Leiden, "GraphL", "leiden", "leiden_community"),
    (Louvain, "GraphV", "louvain", "louvain_community"),
])
def test_cluster_calculate_query_contains_expected_parts(monkeypatch, ClusterClass, graph_name, expected_call, expected_writeprop):
    captured = {}

    def fake_run(self, query, parameters=None):
        captured['query'] = query
        return [(None, None, 'OK')]

    monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

    cluster_instance = ClusterClass()
    cluster_instance.detect_communities(graph_name, "weight_prop")

    q_lower = captured['query'].lower()

    # Проверяем вызов правильного алгоритма GDS
    assert re.search(rf"call\s+gds\.{expected_call}\.write", q_lower)
    # Проверяем, что результат пишется в нужное поле
    assert re.search(rf"writeproperty\s*:\s*'{expected_writeprop}'", q_lower)

@pytest.mark.parametrize("MetricClass,graph_name,weight_prop,expected_call,expected_writeprop", [
    (PageRank, "GraphA", "weight_prop", "pagerank", "pagerank"),
    (Betweenness, "GraphB", "w", "betweenness", "betweenness"),
])
def test_metric_calculate_query_contains_expected_parts(monkeypatch, MetricClass, graph_name, weight_prop, expected_call, expected_writeprop):
    captured = {}

    def fake_run(self, query, parameters=None):
        captured['query'] = query
        return ['OK']

    monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

    metric_instance = MetricClass()
    metric_instance.metric_calculate(graph_name, weight_prop)

    q_lower = captured['query'].lower()

    # Проверяем вызов GDS
    assert re.search(rf"call\s+gds\.{expected_call}\.write", q_lower)
    # Проверяем свойство веса ребра
    assert re.search(rf"relationshipweightproperty\s*:\s*'{weight_prop}'", q_lower)
    # Проверяем, куда пишется результат
    assert re.search(rf"writeproperty\s*:\s*'{expected_writeprop}'", q_lower)
