from app.database.neo4j_connection import Neo4jConnection
"""
    Класс содержащий query для вычисления кластеризации сети 
"""


class CommunityDetection:
    def __init__(self, algorithm_name, property_name):
        self.algorithm_name = algorithm_name
        self.property_name = property_name
        self.connection = Neo4jConnection()

    def detect_communities(
            self,
            graph_name,
            relationship_weight_property
    ):
        self.__detect_communities(graph_name, relationship_weight_property)
        return self.__write_communities(graph_name)

    def __detect_communities(self, graph_name, relationship_weight_property):
        query = f'''
            CALL gds.{self.algorithm_name}.stream(
                '{graph_name}',
                {{
                    relationshipWeightProperty: '{relationship_weight_property}'
                }}
            )
            YIELD nodeId, communityId
            RETURN communityId, COUNT(DISTINCT nodeId) AS members
            ORDER BY members DESC
        '''
        return self.connection.run(query)

    def __write_communities(self, graph_name):
        query = f'''
            CALL gds.{self.algorithm_name}.write(
                '{graph_name}', 
                {{
                    writeProperty: '{self.property_name}'
                }}
            ) 
            YIELD communityCount, modularity, modularities
        '''
        return self.connection.execute_query(query).records[0][2]


class Leiden(CommunityDetection):
    def __init__(self):
        super().__init__("leiden", "leiden_community")


class Louvain(CommunityDetection):
    def __init__(self):
        super().__init__("louvain", "louvain_community")