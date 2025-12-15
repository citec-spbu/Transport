import pytest
from app.core.metric_cluster.metrics_calculate import MetricsCalculate, PageRank, Betweenness
from app.database import neo4j_connection


class TestMetricsCalculate:
    """Тесты для классов расчёта метрик графа."""

    def test_pagerank_initialization(self):
        """Проверяет инициализацию PageRank с правильными параметрами."""
        pr = PageRank()
        assert pr.metric_name == "pagerank"
        assert pr.write_property == "pagerank"

    def test_betweenness_initialization(self):
        """Проверяет инициализацию Betweenness с правильными параметрами."""
        bc = Betweenness()
        assert bc.metric_name == "betweenness"
        assert bc.write_property == "betweenness"

    def test_pagerank_metric_calculate(self, monkeypatch):
        """Проверяет вызов расчёта PageRank с корректными параметрами."""
        captured = {}

        def fake_run(self, query, parameters=None):
            captured['query'] = query
            return []

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        pr = PageRank()
        pr.metric_calculate("GraphPR", "weight_prop")

        q_lower = captured['query'].lower()
        assert "pagerank.write" in q_lower
        assert "weight_prop" in captured['query']
        assert "writeproperty" in q_lower
        assert "pagerank" in q_lower

    def test_betweenness_metric_calculate(self, monkeypatch):
        """Проверяет вызов расчёта Betweenness с корректными параметрами."""
        captured = {}

        def fake_run(self, query, parameters=None):
            captured['query'] = query
            return []

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        bc = Betweenness()
        bc.metric_calculate("GraphBC", "edge_weight")

        q_lower = captured['query'].lower()
        assert "betweenness.write" in q_lower
        assert "edge_weight" in captured['query']
        assert "writeproperty" in q_lower
        assert "betweenness" in q_lower

    def test_metric_calculate_exception_propagates(self, monkeypatch):
        """Проверяет, что исключения при расчёте метрик пробрасываются."""
        def bad_run(self, query, parameters=None):
            raise RuntimeError("GDS metric calculation failed")

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', bad_run)

        pr = PageRank()
        with pytest.raises(RuntimeError, match="GDS metric calculation failed"):
            pr.metric_calculate("Graph", "weight")

    def test_base_class_metric_calculate(self, monkeypatch):
        """Проверяет базовый класс MetricsCalculate."""
        captured = {}

        def fake_run(self, query, parameters=None):
            captured['query'] = query
            return []

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        # Создаём экземпляр базового класса напрямую
        metric = MetricsCalculate("custom_metric", "custom_prop")
        metric.metric_calculate("GraphCustom", "w")

        assert "custom_metric.write" in captured['query'].lower()
        assert "custom_prop" in captured['query']

    def test_multiple_metrics_different_graphs(self, monkeypatch):
        """Проверяет расчёт разных метрик для разных графов."""
        queries = []

        def fake_run(self, query, parameters=None):
            queries.append(query)
            return []

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        pr = PageRank()
        bc = Betweenness()

        pr.metric_calculate("Graph1", "w1")
        bc.metric_calculate("Graph2", "w2")

        assert len(queries) == 2
        assert "Graph1" in queries[0]
        assert "Graph2" in queries[1]
        assert "pagerank" in queries[0].lower()
        assert "betweenness" in queries[1].lower()
