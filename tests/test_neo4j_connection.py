import pytest
from unittest.mock import Mock, MagicMock, patch
from app.database.neo4j_connection import Neo4jConnection


class TestNeo4jConnection:
    """Тесты для класса Neo4jConnection."""

    def test_initialization_creates_driver(self, monkeypatch):
        """Проверяет, что при инициализации создаётся драйвер Neo4j."""
        mock_driver = Mock()
        mock_graph_database = Mock(return_value=mock_driver)

        with patch('app.database.neo4j_connection.GraphDatabase.driver', mock_graph_database):
            conn = Neo4jConnection()
            assert conn.driver == mock_driver
            mock_graph_database.assert_called_once()

    def test_close_closes_driver(self, monkeypatch):
        """Проверяет, что метод close закрывает драйвер."""
        mock_driver = Mock()
        mock_graph_database = Mock(return_value=mock_driver)

        with patch('app.database.neo4j_connection.GraphDatabase.driver', mock_graph_database):
            conn = Neo4jConnection()
            conn.close()
            mock_driver.close.assert_called_once()

    def test_run_executes_query(self, monkeypatch):
        """Проверяет выполнение запроса через run."""
        mock_result = [{"value": 42}]
        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.return_value.data.return_value = mock_result
        mock_driver = Mock()
        mock_driver.session.return_value = mock_session

        with patch('app.database.neo4j_connection.GraphDatabase.driver', return_value=mock_driver):
            conn = Neo4jConnection()
            result = conn.run("RETURN 42 AS value")
            
            assert result == mock_result
            mock_session.__enter__.return_value.run.assert_called_once_with("RETURN 42 AS value", None)

    def test_run_with_parameters(self, monkeypatch):
        """Проверяет выполнение запроса с параметрами."""
        mock_result = [{"name": "Alice"}]
        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.return_value.data.return_value = mock_result
        mock_driver = Mock()
        mock_driver.session.return_value = mock_session

        with patch('app.database.neo4j_connection.GraphDatabase.driver', return_value=mock_driver):
            conn = Neo4jConnection()
            params = {"name": "Alice"}
            result = conn.run("MATCH (n {name: $name}) RETURN n", params)
            
            assert result == mock_result
            mock_session.__enter__.return_value.run.assert_called_once_with(
                "MATCH (n {name: $name}) RETURN n", 
                {"name": "Alice"}
            )

    def test_read_all_returns_records(self, monkeypatch):
        """Проверяет, что read_all возвращает все записи."""
        mock_records = [{"id": 1}, {"id": 2}, {"id": 3}]
        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.return_value = mock_records
        mock_driver = Mock()
        mock_driver.session.return_value = mock_session

        with patch('app.database.neo4j_connection.GraphDatabase.driver', return_value=mock_driver):
            conn = Neo4jConnection()
            result = conn.read_all("MATCH (n) RETURN n")
            
            assert result == mock_records

    def test_read_all_with_parameters(self, monkeypatch):
        """Проверяет read_all с параметрами."""
        mock_records = [{"name": "Bob", "age": 30}]
        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.return_value = mock_records
        mock_driver = Mock()
        mock_driver.session.return_value = mock_session

        with patch('app.database.neo4j_connection.GraphDatabase.driver', return_value=mock_driver):
            conn = Neo4jConnection()
            params = {"min_age": 25}
            result = conn.read_all("MATCH (n) WHERE n.age >= $min_age RETURN n", params)
            
            assert result == mock_records
            mock_session.__enter__.return_value.run.assert_called_once_with(
                "MATCH (n) WHERE n.age >= $min_age RETURN n",
                {"min_age": 25}
            )

    def test_context_manager_closes_connection(self, monkeypatch):
        """Проверяет, что контекстный менеджер закрывает соединение."""
        mock_driver = Mock()
        with patch('app.database.neo4j_connection.GraphDatabase.driver', return_value=mock_driver):
            with Neo4jConnection() as conn:
                pass
            mock_driver.close.assert_called_once()

    def test_run_exception_propagates(self, monkeypatch):
        """Проверяет, что исключения при выполнении запроса пробрасываются."""
        mock_session = MagicMock()
        mock_session.__enter__.return_value.run.side_effect = RuntimeError("Connection failed")
        mock_driver = Mock()
        mock_driver.session.return_value = mock_session

        with patch('app.database.neo4j_connection.GraphDatabase.driver', return_value=mock_driver):
            conn = Neo4jConnection()
            with pytest.raises(RuntimeError, match="Connection failed"):
                conn.run("INVALID QUERY")
