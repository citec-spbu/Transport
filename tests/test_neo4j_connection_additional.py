import pytest
from unittest.mock import patch

from app.database.neo4j_connection import Neo4jConnection


class _DummySession:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute_write(self, fn, *args, **kwargs):
        return fn(self, *args, **kwargs)

    def run(self, query, parameters=None):
        return [self.value]


class _DummyDriver:
    def __init__(self, value):
        self.value = value

    def session(self):
        return _DummySession(self.value)

    def close(self):
        self.closed = True


def test_init_handles_driver_creation_error():
    with patch("app.database.neo4j_connection.GraphDatabase.driver", side_effect=RuntimeError("boom")):
        conn = Neo4jConnection()
        assert conn._Neo4jConnection__driver is None
        with pytest.raises(AssertionError):
            conn.run("RETURN 1")


def test_execute_write_happy_path():
    with patch("app.database.neo4j_connection.GraphDatabase.driver", return_value=_DummyDriver(value={"x": 1})):
        conn = Neo4jConnection()

        def tx_func(tx, arg):
            return (tx.run("RETURN $x", {"x": arg}), arg)

        result = conn.execute_write(tx_func, 5)
        assert result == ([{"x": 1}], 5)
