from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

import pandas as pd

from app.database.neo4j_connection import Neo4jConnection

if TYPE_CHECKING:
    from app.core.context.analysis_context import AnalysisContext


class GraphDBManager(ABC):
    def __init__(self, analysis_context: "AnalysisContext"):
        self.connection = Neo4jConnection()
        self.city_name = analysis_context.city_name
        self.enrich_db_parameters(analysis_context)
        self.db_graph_parameters = analysis_context.db_graph_parameters

    def enrich_db_parameters(self, analysis_context: "AnalysisContext"):
        analysis_context.db_graph_parameters.city_name = self.city_name
        analysis_context.db_graph_parameters.node_geometry_identity = self.node_geometry_identity()
        analysis_context.db_graph_parameters.main_rels_name = self.get_main_rels_name()
        analysis_context.db_graph_parameters.main_node_name = self.get_main_node_name()
        analysis_context.db_graph_parameters.weight = self.get_weight()

    @abstractmethod
    def get_graph(self):
        pass

    @abstractmethod
    def get_weight(self) -> str:
        pass

    @abstractmethod
    def get_main_node_name(self) -> str:
        pass

    @abstractmethod
    def get_main_rels_name(self) -> str:
        pass

    @abstractmethod
    def node_geometry_identity(self) -> str:
        pass


class OneTypeNodeDBManager(GraphDBManager):
    def __init__(self, analysis_context: "AnalysisContext"):
        super().__init__(analysis_context)

    @abstractmethod
    def get_bd_all_node_query_graph(self) -> str:
        pass

    @abstractmethod
    def get_bd_all_rels_query_graph(self) -> str:
        pass

    @abstractmethod
    def get_node_name(self) -> str:
        pass

    @abstractmethod
    def get_rels_name(self) -> str:
        pass

    @abstractmethod
    def get_constraint_list(self) -> List[str]:
        pass

    @abstractmethod
    def create_node_query(self) -> str:
        pass

    @abstractmethod
    def create_relationships_query(self) -> str:
        pass

    def update_db(self, city_name):
        (nodes, relationships) = self.get_graph()
        if nodes is None and relationships is None:
            print("Graph for", city_name, "is empty!")
            return
        self.connection.execute_write(self.create_constraints)
        self.connection.execute_write(insert_data, self.create_node_query(), nodes)
        self.connection.execute_write(insert_data, self.create_relationships_query(), relationships)

    def get_bd_all_node_graph(self):
        query = self.get_bd_all_node_query_graph()
        return self.connection.read_all(query)

    def get_bd_all_rels_graph(self):
        query = self.get_bd_all_rels_query_graph()
        return self.connection.read_all(query)

    def create_constraints(self, tx):
        for constraint in self.get_constraint_list():
            tx.run(constraint)

    def get_main_node_name(self):
        return self.get_node_name().replace('-', '')

    def get_main_rels_name(self):
        return self.get_rels_name().replace('-', '')


def insert_data(tx, query: str, rows: List[dict], batch_size: int = 10000) -> int:
    if not rows:
        return 0

    total = 0
    df = pd.DataFrame(rows)
    batch = 0

    while batch * batch_size < len(df):
        current_batch = df.iloc[batch * batch_size:(batch + 1) * batch_size]
        batch_data = current_batch.to_dict('records')
        results = tx.run(query, parameters={'rows': batch_data}).data()
        total += results[0]['total'] if results else 0
        batch += 1
    return total
