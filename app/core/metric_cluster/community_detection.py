from app.database.neo4j_connection import Neo4jConnection

"""
    Классы для вычисления и записи кластеров в Neo4j (GDS)
"""

class CommunityDetection:
    def __init__(self, algorithm_name: str, property_name: str):
        self.algorithm_name = algorithm_name
        self.property_name = property_name
        self.connection = Neo4jConnection()

    def detect_communities(
        self,
        graph_name: str,
        relationship_weight_property: str
    ):
        query = f'''
            CALL gds.{self.algorithm_name}.write(
                '{graph_name}',
                {{
                    relationshipWeightProperty: '{relationship_weight_property}',
                    writeProperty: '{self.property_name}'
                }}
            )
            YIELD communityCount, modularity, modularities
        '''

        result = self.connection.execute_query(query).records[0]
        return {
            "community_count": result["communityCount"],
            "modularity": result["modularity"],
            "modularities": result["modularities"],
        }


class Leiden(CommunityDetection):
    def __init__(self):
        super().__init__("leiden", "leiden_community")


class Louvain(CommunityDetection):
    def __init__(self):
        super().__init__("louvain", "louvain_community")
