from neo4j import GraphDatabase, Session
from dotenv import load_dotenv
import os
from functools import wraps
from typing import Callable, Optional, Dict

"""
    Класс, содержащий логику работы с Neo4j.
"""


def with_session(func: Callable):
    """
    Декоратор для автоматического создания и закрытия сессии.
    Используется для методов run(), execute_write() и т.д.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        assert self._driver is not None, "Driver not initialized!"
        session: Optional[Session] = None

        try:
            session = self._driver.session()
            return func(self, session, *args, **kwargs)
        except Exception as e:
            print(f"Neo4j error in {func.__name__}: {e}")
            raise
        finally:
            if session is not None:
                session.close()

    return wrapper


class Neo4jConnection:
    def __init__(self):
        load_dotenv()

        self._uri = os.getenv("GRAPH_DATABASE_URL")
        self._user = os.getenv("GRAPH_DATABASE_USER")
        self._pwd = os.getenv("GRAPH_DATABASE_PASSWORD")

        self._driver = None

        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._pwd)
            )
        except Exception as e:
            print("Failed to create the Neo4j driver:", e)

    def close(self):
        if self._driver:
            self._driver.close()

    # -----------------------------
    # Унифицированные методы
    # -----------------------------

    @with_session
    def run(self, session: Session, query: str, parameters: Dict = None):
        result = session.run(query, parameters)
        return list(result)

    @with_session
    def execute_query(self, session: Session, query: str, parameters: Dict = None, need_log: bool = True):
        result = session.execute_query(query, parameters=parameters)
        if need_log:
            print(result.records)
        return result

    @with_session
    def execute_read(self, session: Session, tx_func: Callable, *args, **kwargs):
        return session.execute_read(tx_func, *args, **kwargs)

    @with_session
    def execute_write(self, session: Session, tx_func: Callable, *args, **kwargs):
        return session.execute_write(tx_func, *args, **kwargs)
