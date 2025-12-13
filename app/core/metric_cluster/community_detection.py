from app.database.neo4j_connection import Neo4jConnection
import logging

logger = logging.getLogger(__name__)

class CommunityDetection:
    def __init__(self, algorithm_name: str, property_name: str):
        """
        Initialize the CommunityDetection instance and prepare a Neo4j connection.
        
        Parameters:
            algorithm_name (str): Name of the GDS community detection algorithm to use (e.g., "leiden", "louvain").
            property_name (str): Node property name where detected community ids will be written.
        
        Notes:
            - Creates a Neo4jConnection and assigns it to `self.connection`.
            - Initializes `self.graph_name` to None until `detect_communities` is called.
        """
        self.algorithm_name = algorithm_name
        self.property_name = property_name
        self.connection = Neo4jConnection()
        self.graph_name = None

    def detect_communities(self, graph_name: str, relationship_weight_property: str) -> None:
        """
        Detects and writes community assignments for the specified in-memory graph using the configured algorithm.
        
        Parameters:
            graph_name (str): Name of the in-memory graph to run the algorithm against.
            relationship_weight_property (str): Relationship property to use as the edge weight for community computation.
        """
        self.graph_name = graph_name
        self._write_communities(graph_name, relationship_weight_property)

    def _write_communities(self, graph_name: str, relationship_weight_property: str) -> None:
        """
        Write community assignments produced by the configured GDS algorithm into the specified in-memory graph.
        
        Parameters:
            graph_name (str): Name of the in-memory graph in the Neo4j GDS catalog to run the write procedure against.
            relationship_weight_property (str): Relationship property name to use as the weight for the algorithm.
        """
        query = f'''
            CALL gds.{self.algorithm_name}.write(
                '{graph_name}',
                {{
                    relationshipWeightProperty: '{relationship_weight_property}',
                    writeProperty: '{self.property_name}'
                }}
            )
        '''
        try:
            self.connection.run(query)
        except Exception as e:
            logger.error(f"Error writing communities: {e}")

    def _get_metric(self, query: str) -> float:
        """
        Execute a Cypher query and return the numeric value from its first column of the first row.
        
        Parameters:
            query (str): Cypher query expected to yield a single numeric value in the first column of the first row.
        
        Returns:
            float: The numeric metric from the query's first column and first row, or 0.0 if self.graph_name is not set, the result is missing/None, or an error occurs.
        """
        if not self.graph_name:
            return 0.0
        try:
            result = self.connection.run(query)
            if result and result[0][0] is not None:
                return float(result[0][0])
        except Exception as e:
            logger.error(f"Error executing metric query: {e}")
        return 0.0

    def calculate_modularity(self) -> float:
        """
        Compute the modularity score for the currently configured graph and algorithm.
        
        Returns:
            modularity (float): The modularity score for the graph. Returns 0.0 if no graph is configured or the metric cannot be retrieved.
        """
        query = f"CALL gds.{self.algorithm_name}.stats('{self.graph_name}') YIELD modularity RETURN modularity"
        return self._get_metric(query)

    def calculate_silhouette(self) -> float:
        """
        Compute the silhouette score for the currently set graph using the configured algorithm.
        
        Returns:
            float: Average silhouette score for the graph (typically between -1.0 and 1.0). Returns 0.0 if no graph is set or the metric cannot be retrieved.
        """
        query = f'''
            CALL gds.{self.algorithm_name}.stats(
                '{self.graph_name}',
                {{ computeSilhouette: true }}
            ) YIELD silhouette RETURN silhouette
        '''
        return self._get_metric(query)

    def calculate_conductance(self) -> float:
        """
        Compute the average conductance across communities for the configured graph.
        
        Calls the GDS conductance stream for the instance's graph and returns the mean conductance over all communities.
        
        Returns:
            avg_conductance (float): Average conductance across communities; returns 0.0 if the instance has no graph configured or if the query fails.
        """
        query = f'''
            CALL gds.alpha.conductance.stream('{self.graph_name}')
            YIELD communityId, conductance
            RETURN AVG(conductance) AS avg_conductance
        '''
        return self._get_metric(query)

    def calculate_coverage(self) -> float:
        """
        Compute the average coverage of detected communities for the current graph.
        
        Returns:
            avg_coverage (float): The mean coverage across communities, or 0.0 if the graph name is not set or the metric cannot be retrieved.
        """
        query = f'''
            CALL gds.alpha.coverage.stream('{self.graph_name}')
            YIELD communityId, coverage
            RETURN AVG(coverage) AS avg_coverage
        '''
        return self._get_metric(query)


class Leiden(CommunityDetection):
    def __init__(self):
        super().__init__("leiden", "leiden_community")


class Louvain(CommunityDetection):
    def __init__(self):
        """
        Initialize a CommunityDetection configured to run the Louvain algorithm and write detected community ids to the 'louvain_community' node property.
        """
        super().__init__("louvain", "louvain_community")