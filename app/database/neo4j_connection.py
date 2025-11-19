from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

"""
    Класс содержащий логику работы с бд neo4j
"""


class Neo4jConnection:
    def __init__(self):
        load_dotenv()
        os.environ.get("DB_HOST", "localhost")

        self.__uri = os.environ.get("GRAPH_DATABASE_URL")
        self.__user = os.environ.get("GRAPH_DATABASE_USER")
        self.__pwd = os.environ.get("GRAPH_DATABASE_PASSWORD")
        self.__driver = None

        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):

        if self.__driver is not None:
            self.__driver.close()

    # TODO: need to add decorator for run and execute_write
    def run(self, query, parameters=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None

        try:
            session = self.__driver.session()
            result = session.run(query, parameters)
            print(list(result))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()

    def execute_query(self, query, needLog=True):
        assert self.__driver is not None, "Driver not initialized!"
        session = None

        try:
            result = self.__driver.execute_query(query)
            if needLog: print(list(result))
            return result
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()

    def read_all(self, query):
        assert self.__driver is not None, "Driver not initialized!"
        session = None

        try:
            session = self.__driver.session()
            result = session.execute_read(get_node, query)
            return result
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()

    def execute_write(self, transaction_function, *args):
        assert self.__driver is not None, "Driver not initialized!"
        session = None

        try:
            session = self.__driver.session()
            session.execute_write(transaction_function, *args)
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()


def get_node(tx, query, bounds=None):
    results = tx.run(query, parameters=bounds).to_df()
    return results
