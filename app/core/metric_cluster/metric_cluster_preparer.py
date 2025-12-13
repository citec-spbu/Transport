from app.core.context.analysis_context import AnalysisContext
from app.core.metric_cluster.community_detection import Leiden, Louvain
from app.core.metric_cluster.metrics_calculate import Betweenness, PageRank
from app.database.neo4j_connection import Neo4jConnection


class MetricClusterPreparer:

    def __init__(self, analysis_context: AnalysisContext):
        """
        Initialize the preparer with an analysis context, establish a Neo4j connection, and create metric/cluster calculators according to the context's flags.
        
        Parameters:
            analysis_context (AnalysisContext): Context containing graph, parameters, and metric calculation flags; used to populate `self.ctx`, `self.mc`, and to determine which metric and clustering calculator instances to create (Leiden, Louvain, Betweenness, PageRank).
        """
        self.ctx = analysis_context
        self.conn = Neo4jConnection()

        self.mc = analysis_context.metric_calculation_context

        self.leiden = Leiden() if self.mc.need_leiden_clusterization else None
        self.louvain = Louvain() if self.mc.need_louvain_clusterization else None
        self.betweenness = Betweenness() if self.mc.need_betweenness else None
        self.pagerank = PageRank() if self.mc.need_pagerank else None

    def prepare_metrics(self) -> dict:

        """
        Prepare and return graph node metrics and optional cluster statistics for the current analysis context.
        
        This method conditionally computes clustering and centrality metrics (Leiden, Louvain, betweenness, PageRank) according to the preparer's configuration, loads nodes annotated with the computed metrics, and assembles the results. When Leiden or Louvain clustering is enabled, cluster-level statistics (modularity, silhouette, conductance, coverage) are included.
        
        Returns:
            result (dict): A dictionary with keys:
                - "nodes" (list[dict]): Node objects containing id, name, coordinates and any requested metric or cluster fields.
                - "statistics" (dict | None): Cluster statistics dictionary with keys "modularity", "silhouette", "conductance", and "coverage" when clustering was performed; omitted or None when no clustering detector is active.
        """
        if self.leiden:
            self._run_leiden()

        if self.louvain:
            self._run_louvain()

        if self.betweenness:
            self._run_betweenness()

        if self.pagerank:
            self._run_pagerank()

        nodes = self._load_nodes_with_metrics()

        result = {"nodes": nodes}
        
        if self.leiden or self.louvain:
            result["statistics"] = self._calculate_cluster_statistics()
        
        return result

    # -------------------- Метрики --------------------

    def _run_leiden(self):
        self.leiden.detect_communities(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    def _run_louvain(self):
        self.louvain.detect_communities(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    def _run_betweenness(self):
        self.betweenness.metric_calculate(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    def _run_pagerank(self):
        self.pagerank.metric_calculate(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    # -------------------- Получение узлов --------------------

    def _load_nodes_with_metrics(self) -> list[dict]:

        """
        Collects nodes from the configured graph and returns their identifiers, names, coordinates, and any requested cluster or metric values.
        
        When Leiden or Louvain clustering is enabled, each returned node includes a 'cluster_id' set to that detector's community identifier. When betweenness or PageRank is enabled, each returned node includes a 'metric' set to the requested metric value. Nodes that lack any required cluster or metric field for enabled analyses are omitted.
        
        Returns:
            list[dict]: List of node dictionaries. Each dictionary contains:
                - 'id' (str): Node element identifier.
                - 'name' (str): Node name.
                - 'coordinates' (list[float]): [longitude, latitude].
                - 'cluster_id' (int|str, optional): Community identifier when clustering is requested.
                - 'metric' (float, optional): Metric value when betweenness or PageRank is requested.
        """
        node_label = self.ctx.db_graph_parameters.main_node_name

        query = f"""
            MATCH (n:`{node_label}`)
            RETURN
                elementId(n) AS id,
                n.name AS name,
                n.location.longitude AS lon,
                n.location.latitude AS lat,
                n.leiden_community AS leiden_community,
                n.louvain_community AS louvain_community,
                n.betweenness AS betweenness,
                n.pagerank AS pagerank
        """

        rows = self.conn.read_all(query)

        result = []
        for r in rows:
            node = {
                "id": r["id"],
                "name": r["name"],
                "coordinates": [r["lon"], r["lat"]],
            }

            if self.mc.need_leiden_clusterization:
                if r["leiden_community"] is not None:
                    node["cluster_id"] = (
                        r["leiden_community"]
                    )
                else:
                    continue

            if self.mc.need_louvain_clusterization:
                if r["louvain_community"] is not None:
                    node["cluster_id"] = (
                        r["louvain_community"]
                    )
                else:
                    continue

            if self.mc.need_betweenness:
                if r["betweenness"] is not None:
                    node["metric"] = r["betweenness"]
                else:
                    continue

            if self.mc.need_pagerank:
                if r["pagerank"] is not None:
                    node["metric"] = r["pagerank"]
                else:
                    continue

            result.append(node)

        return result

    # -------------------- Статистика кластеризации --------------------

    def _calculate_cluster_statistics(self) -> dict:
        """
        Compute clustering quality statistics using the active cluster detector (Leiden or Louvain).
        
        Returns:
            dict: Mapping with the following keys:
                - "modularity": Modularity score of the current clustering, or `None` if no detector is available.
                - "silhouette": Silhouette score of the clustering, or `None` if no detector is available.
                - "conductance": Conductance of the clustering, or `None` if no detector is available.
                - "coverage": Coverage of the clustering, or `None` if no detector is available.
        """
        detector = self.leiden if self.leiden else self.louvain
        
        if not detector:
            return {
                "modularity": None,
                "silhouette": None,
                "conductance": None,
                "coverage": None
            }
        
        detector.graph_name = self.ctx.graph_name
        
        return {
            "modularity": detector.calculate_modularity(),
            "silhouette": detector.calculate_silhouette(),
            "conductance": detector.calculate_conductance(),
            "coverage": detector.calculate_coverage()
        }