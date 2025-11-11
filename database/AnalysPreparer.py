from urban_transit_network_analysis.database.Neo4jConnection import Neo4jConnection

from context import GraphAnalisContext


class AnalysPreparer:
    def __init__(self, graph_analisis_context: GraphAnalisContext):
        self.connection = Neo4jConnection()
        self.graph_db_parameters = graph_analisis_context.neo4j_DB_graph_parameters
        self.graph_name = graph_analisis_context.graph_name

    def prepare(self):
        self.make_graph()

    def make_graph(self):
        # First, create a normalized relationship property to avoid modifying the original
        rel_name = self.graph_db_parameters.main_rels_name
        weight_prop = self.graph_db_parameters.weight

        normalize_query = f"""
            MATCH ()-[r:`{rel_name}`]->()
            WHERE r.{weight_prop} IS NOT NULL
            SET r.norm_{weight_prop} = log(1 + r.{weight_prop})
            RETURN count(r) AS normalized_count
        """
        try:
            self.connection.run(normalize_query)
        except Exception:
            # Log and continue; projection has defaultValue as a fallback
            print(f"Warning: normalization query failed for {rel_name}.{weight_prop}")

        # Use the normalized property for projection and metric calculations
        normalized_prop = f"norm_{weight_prop}"
        # Update context parameter so downstream metric calculators use normalized weight
        self.graph_db_parameters.weight = normalized_prop

        # Then create the GDS projection using the normalized property and MIN aggregation
        query = f'''
            CALL gds.graph.project(
            '{self.graph_name}',
            '{self.graph_db_parameters.main_node_name}',
            {{
                `{self.graph_db_parameters.main_rels_name}`: {{
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
        '''
        self.connection.run(query)