import re

from app.core.metric_cluster.metrics_calculate import PageRank, Betweenness
from app.database import neo4j_connection


def test_pagerank_query_contains_expected_parts(monkeypatch):
    captured = {}

    def fake_run(self, query, parameters=None):
        captured['query'] = query
        return ['OK']

    monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

    pr = PageRank()
    res = pr.metric_calculate('MyGraph', 'weight_prop')

    assert res == ['OK']
    q = captured['query']
    assert "CALL gds.pageRank.write" in q or "CALL gds.pageRank.write".lower() in q.lower()
    assert "relationshipWeightProperty: 'weight_prop'" in q
    assert "writeProperty: 'pagerank'" in q


def test_betweenness_query_contains_expected_parts(monkeypatch):
    captured = {}

    def fake_run(self, query, parameters=None):
        captured['query'] = query
        return ['OK']

    monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

    bt = Betweenness()
    res = bt.metric_calculate('GraphB', 'w')

    assert res == ['OK']
    q = captured['query']
    assert "CALL gds.betweenness.write" in q
    assert "relationshipWeightProperty: 'w'" in q
    assert "writeProperty: 'betweenness'" in q
