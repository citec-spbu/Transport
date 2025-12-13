from app.database.neo4j_connection import Neo4jConnection
from app.core.context.analysis_context import AnalysisContext

class AnalysisPreparer:
    def __init__(self, analysis_context: AnalysisContext):
        self.connection = Neo4jConnection()
        self.graph_db_parameters = analysis_context.db_graph_parameters
        self.graph_name = analysis_context.graph_name

    def prepare(self):
        """Готовит данные графа к анализу.

        Нормализует веса отношений и строит проекцию GDS
        с использованием нормализованного свойства веса.
        """
        rel_name = self.graph_db_parameters.main_rels_name
        weight_prop = self.graph_db_parameters.weight

        # Нормализация весов
        normalize_query = f"""
            MATCH ()-[r:`{rel_name}`]->()
            WHERE r.{weight_prop} IS NOT NULL
            SET r.norm_{weight_prop} = log(1 + r.{weight_prop})
            RETURN count(r) AS normalized_count
        """
        try:
            self.connection.run(normalize_query)
        except Exception as e:
            print(f"Warning: normalization query failed for {rel_name}.{weight_prop}: {e}")

        # Используем нормализованное свойство для построения проекции GDS
        normalized_prop = f"norm_{weight_prop}"
        self.graph_db_parameters.weight = normalized_prop

        if not self.graph_db_parameters.main_node_name or not self.graph_db_parameters.main_rels_name:
            raise ValueError("Graph parameters 'main_node_name' or 'main_rels_name' are not set.")

        print(f"Preparing graph with nodes: {self.graph_db_parameters.main_node_name}, relationships: {rel_name}")
        print(f"Normalized weight property: {normalized_prop}")

        graph_project_query = f"""
            CALL gds.graph.project(
                '{self.graph_name}',
                '{self.graph_db_parameters.main_node_name}',
                {{
                    {rel_name}: {{
                        orientation: 'UNDIRECTED',
                        properties: {{
                            {normalized_prop}: {{
                                property: '{normalized_prop}',
                                defaultValue: 1.0,
                                aggregation: 'MIN'
                            }}
                        }}
                    }}
                }}
            )
        """
        try:
            print(f"Graph projection query: {graph_project_query}")
            print(f"Graph parameters: {self.graph_db_parameters}")
            self.connection.run(graph_project_query)
        except Exception as e:
            print(f"Warning: GDS graph projection failed for {self.graph_name}: {e}")
