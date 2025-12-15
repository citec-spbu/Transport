import logging

from app.core.context.analysis_context import AnalysisContext
from app.core.metric_cluster.community_detection import Leiden, Louvain
from app.core.metric_cluster.metrics_calculate import Betweenness, PageRank
from app.database.neo4j_connection import Neo4jConnection


class MetricClusterPreparer:
    """Готовит метрики и кластеры для анализа графа."""

    def __init__(self, analysis_context: AnalysisContext):
        """Инициализирует подготовку метрик на основе контекста анализа."""
        self.ctx = analysis_context
        self.conn = Neo4jConnection()

        self.mc = analysis_context.metric_calculation_context

        self.leiden = Leiden() if self.mc.need_leiden_clusterization else None
        self.louvain = Louvain() if self.mc.need_louvain_clusterization else None
        self.betweenness = Betweenness() if self.mc.need_betweenness else None
        self.pagerank = PageRank() if self.mc.need_pagerank else None

    def prepare_metrics(self) -> dict:
        """Запускает расчёт выбранных метрик и кластеризаций и возвращает результат."""

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
        """Запускает кластеризацию алгоритмом Leiden."""
        self.leiden.detect_communities(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    def _run_louvain(self):
        """Запускает кластеризацию алгоритмом Louvain."""
        self.louvain.detect_communities(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    def _run_betweenness(self):
        """Вычисляет метрику промежуточности (Betweenness)."""
        self.betweenness.metric_calculate(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    def _run_pagerank(self):
        """Вычисляет метрику PageRank."""
        self.pagerank.metric_calculate(
            self.ctx.graph_name,
            self.ctx.db_graph_parameters.weight
        )

    # -------------------- Получение узлов --------------------

    def _load_nodes_with_metrics(self) -> list[dict]:
        """Загружает узлы с рассчитанными метриками и метками кластеров."""

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
        """Рассчитывает агрегированные показатели качества кластеризации.

        Возвращает словарь с метриками: модульность, проводимость и покрытие. 
        При ошибке возвращает -1.0 для каждой метрики.
        """
        detector = self.leiden if self.leiden else self.louvain

        if not detector:
            raise ValueError("Cluster detector is not initialized; run clustering first")

        detector.graph_name = self.ctx.graph_name

        try:
            return {
                "modularity": detector.calculate_modularity(),
                "conductance": detector.calculate_conductance(),
                "coverage": detector.calculate_coverage()
            }
        except Exception:
            logger = logging.getLogger(__name__)
            logger.exception("Error calculating cluster statistics")
            raise
