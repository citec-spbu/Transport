from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

class Neo4jConnection:
    def __init__(self):
        load_dotenv()
        self.__uri = os.environ.get("GRAPH_DATABASE_URL")
        self.__user = os.environ.get("GRAPH_DATABASE_USER")
        self.__pwd = os.environ.get("GRAPH_DATABASE_PASSWORD")
        self.__driver = None

        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver:
            self.__driver.close()

    def run(self, query, parameters=None):
        """Выполнить запрос и вернуть все строки как список"""
        assert self.__driver, "Driver not initialized!"
        with self.__driver.session() as session:
            result = session.run(query, parameters)
            return list(result)

    def read_all(self, query, parameters=None):
        """Выполнить read-запрос и вернуть список словарей"""
        assert self.__driver, "Driver not initialized!"
        def read_tx(tx):
            result = tx.run(query, parameters)
            return [dict(record) for record in result]
        with self.__driver.session() as session:
            return session.execute_read(read_tx)

    def execute_write(self, tx_func, *args, **kwargs):
        """Выполнить write-транзакцию"""
        assert self.__driver, "Driver not initialized!"
        with self.__driver.session() as session:
            return session.execute_write(tx_func, *args, **kwargs)
