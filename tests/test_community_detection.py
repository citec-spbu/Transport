import pytest
from app.core.metric_cluster.community_detection import CommunityDetection, Leiden, Louvain
from app.database import neo4j_connection


@pytest.fixture(autouse=True)
def patch_neo4j_conn(monkeypatch):
    """Отключает реальное подключение Neo4j в тестах."""
    def fake_init(self):
        self.driver = None
    monkeypatch.setattr(neo4j_connection.Neo4jConnection, "__init__", fake_init)


class TestCommunityDetection:
    """Тесты для базового класса CommunityDetection и его подклассов."""

    def test_leiden_initialization(self):
        """Проверяет инициализацию Leiden с правильными параметрами."""
        leiden = Leiden()
        assert leiden.algorithm_name == "leiden"
        assert leiden.property_name == "leiden_community"
        assert leiden.graph_name is None

    def test_louvain_initialization(self):
        """Проверяет инициализацию Louvain с правильными параметрами."""
        louvain = Louvain()
        assert louvain.algorithm_name == "louvain"
        assert louvain.property_name == "louvain_community"
        assert louvain.graph_name is None

    def test_detect_communities_calls_write(self, monkeypatch):
        """Проверяет, что detect_communities устанавливает graph_name и вызывает запись."""
        captured_query = {}

        def fake_run(self, query, parameters=None):
            captured_query['query'] = query
            return []

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        leiden = Leiden()
        leiden.detect_communities("TestGraph", "weight_prop")

        assert leiden.graph_name == "TestGraph"
        assert "leiden.write" in captured_query['query'].lower()
        assert "weight_prop" in captured_query['query']
        assert "leiden_community" in captured_query['query']

    def test_write_communities_exception_propagates(self, monkeypatch):
        """Проверяет, что исключения при записи сообществ пробрасываются."""
        def bad_run(self, query, parameters=None):
            raise RuntimeError("Neo4j write failed")

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', bad_run)

        leiden = Leiden()
        with pytest.raises(RuntimeError, match="Neo4j write failed"):
            leiden.detect_communities("Graph", "weight")

    def test_get_metric_raises_when_no_graph_name(self):
        """Проверяет, что _get_metric выбрасывает ошибку при отсутствии graph_name."""
        leiden = Leiden()
        with pytest.raises(ValueError, match="graph_name is not set"):
            leiden._get_metric("SELECT 1")

    def test_get_metric_raises_on_empty_result(self, monkeypatch):
        """Проверяет, что _get_metric выбрасывает ошибку при пустом результате."""
        def fake_run(self, query, parameters=None):
            return []

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        leiden = Leiden()
        leiden.graph_name = "TestGraph"

        with pytest.raises(ValueError, match="empty result"):
            leiden._get_metric("RETURN 1")

    def test_get_metric_returns_float_value(self, monkeypatch):
        """Проверяет, что _get_metric возвращает корректное значение."""
        def fake_run(self, query, parameters=None):
            return [[0.75]]

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        leiden = Leiden()
        leiden.graph_name = "TestGraph"
        result = leiden._get_metric("RETURN 0.75")

        assert result == 0.75

    def test_calculate_modularity_success(self, monkeypatch):
        """Проверяет успешный расчёт модульности."""
        def fake_run(self, query, parameters=None):
            return [[0.65]]

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        leiden = Leiden()
        leiden.graph_name = "G1"
        modularity = leiden.calculate_modularity()

        assert modularity == 0.65

    def test_calculate_modularity_raises_on_error(self, monkeypatch):
        """Проверяет, что ошибка при расчёте модульности пробрасывается."""
        def bad_run(self, query, parameters=None):
            raise RuntimeError("GDS stats failed")

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', bad_run)

        leiden = Leiden()
        leiden.graph_name = "G1"

        with pytest.raises(RuntimeError, match="GDS stats failed"):
            leiden.calculate_modularity()

    def test_calculate_conductance_success(self, monkeypatch):
        """Проверяет успешный расчёт проводимости."""
        def fake_run(self, query, parameters=None):
            return [[0.12]]

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        louvain = Louvain()
        louvain.graph_name = "G2"
        conductance = louvain.calculate_conductance()

        assert conductance == 0.12

    def test_calculate_conductance_raises_on_error(self, monkeypatch):
        """Проверяет, что ошибка при расчёте проводимости пробрасывается."""
        def bad_run(self, query, parameters=None):
            raise RuntimeError("Conductance query failed")

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', bad_run)

        louvain = Louvain()
        louvain.graph_name = "G2"

        with pytest.raises(RuntimeError, match="Conductance query failed"):
            louvain.calculate_conductance()

    def test_calculate_coverage_success(self, monkeypatch):
        """Проверяет успешный расчёт покрытия."""
        def fake_run(self, query, parameters=None):
            return [[0.88]]

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        leiden = Leiden()
        leiden.graph_name = "G3"
        coverage = leiden.calculate_coverage()

        assert coverage == 0.88

    def test_calculate_coverage_raises_on_error(self, monkeypatch):
        """Проверяет, что ошибка при расчёте покрытия пробрасывается."""
        def bad_run(self, query, parameters=None):
            raise RuntimeError("Coverage query failed")

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', bad_run)

        leiden = Leiden()
        leiden.graph_name = "G3"

        with pytest.raises(RuntimeError, match="Coverage query failed"):
            leiden.calculate_coverage()

    def test_louvain_detect_communities_uses_correct_algorithm(self, monkeypatch):
        """Проверяет, что Louvain использует правильный алгоритм."""
        captured = {}

        def fake_run(self, query, parameters=None):
            captured['query'] = query
            return []

        monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'run', fake_run)

        louvain = Louvain()
        louvain.detect_communities("GraphL", "w")

        assert "louvain.write" in captured['query'].lower()
        assert "louvain_community" in captured['query']
