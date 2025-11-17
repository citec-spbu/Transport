from context.analysis_context import AnalysisContext
from community_detection import Leiden, Louvain
from metrics_calculate import Betweenness, PageRank
from app.database.neo4j_connection import Neo4jConnection


class MetricClusterPreparer:

    def __init__(self, analysis_context: AnalysisContext):
        self.ctx = analysis_context
        self.conn = Neo4jConnection()

        self.mc = analysis_context.metric_calculation_context

        self.leiden = Leiden() if self.mc.need_leiden_clusterization else None
        self.louvain = Louvain() if self.mc.need_louvain_clusterization else None
        self.betweenness = Betweenness() if self.mc.need_betweenness else None
        self.pagerank = PageRank() if self.mc.need_pagerank else None

    def prepare_metrics(self) -> list[dict]:

        if self.leiden:
            self._run_leiden()

        if self.louvain:
            self._run_louvain()

        if self.betweenness:
            self._run_betweenness()

        if self.pagerank:
            self._run_pagerank()

        # Собираем данные из Neo4j и возвращаем
        return self._load_nodes_with_metrics()

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

        node_label = self.ctx.db_graph_parameters.main_node_name

        query = f"""
            MATCH (n:`{node_label}`)
            RETURN
                id(n) AS id,
                n.name AS name,
                n.lat AS lat,
                n.lon AS lon,
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
                "coordinates": [r["lat"], r["lon"]],
            }

            if self.mc.need_leiden_clusterization:
                node["cluster_id"] = (
                    r["leiden_community"]
                )

            if self.mc.need_louvain_clusterization:
                node["cluster_id"] = (
                    r["louvain_community"]
                )

            if self.mc.need_betweenness:
                node["metric"] = r["betweenness"]

            if self.mc.need_pagerank:
                node["metric"] = r["pagerank"]

            result.append(node)

        return result
