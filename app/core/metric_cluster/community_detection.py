from app.database.neo4j_connection import Neo4jConnection
import logging

logger = logging.getLogger(__name__)


class CommunityDetection:
    """Базовый класс для детекции сообществ и расчёта метрик качества кластеризации."""

    def __init__(self, algorithm_name: str, property_name: str):
        """Инициализирует детектор сообществ.

        :param algorithm_name: имя алгоритма GDS (leiden / louvain)
        :param property_name: имя свойства узла для записи идентификатора сообщества
        """
        self.algorithm_name = algorithm_name
        self.property_name = property_name
        self.connection = Neo4jConnection()
        self.graph_name: str | None = None

    def detect_communities(
        self,
        graph_name: str,
        relationship_weight_property: str
    ) -> None:
        """Запускает алгоритм детекции сообществ для указанного графа.

        :param graph_name: имя проецированного графа GDS
        :param relationship_weight_property: свойство рёбер с весами
        """
        self.graph_name = graph_name
        self._write_communities(graph_name, relationship_weight_property)

    def _write_communities(
        self,
        graph_name: str,
        relationship_weight_property: str
    ) -> None:
        """Записывает идентификаторы сообществ в узлы графа."""
        query = f"""
            CALL gds.{self.algorithm_name}.write(
                '{graph_name}',
                {{
                    relationshipWeightProperty: '{relationship_weight_property}',
                    writeProperty: '{self.property_name}'
                }}
            )
        """
        try:
            self.connection.run(query)
        except Exception:
            logger.exception("Error writing communities")
            raise

    def _get_metric(self, query: str) -> float:
        """Выполняет запрос метрики и возвращает значение.

        Безопасно проверяет структуру результата и возвращает 0.0
        при ошибке или пустом результате.
        """
        if not self.graph_name:
            return 0.0

        try:
            result = self.connection.run(query)

            if (
                isinstance(result, (list, tuple))
                and result
                and isinstance(result[0], (list, tuple))
                and result[0]
                and result[0][0] is not None
            ):
                return float(result[0][0])

            return 0.0

        except Exception:
            logger.exception("Error executing metric query")
            return 0.0

    def calculate_modularity(self) -> float:
        """Возвращает значение модульности кластеризации."""
        query = (
            f"CALL gds.{self.algorithm_name}.stats('{self.graph_name}') "
            f"YIELD modularity RETURN modularity"
        )
        return self._get_metric(query)

    def calculate_silhouette(self) -> float:
        """Возвращает значение коэффициента силуэта."""
        query = f"""
            CALL gds.{self.algorithm_name}.stats(
                '{self.graph_name}',
                {{ computeSilhouette: true }}
            )
            YIELD silhouette
            RETURN silhouette
        """
        return self._get_metric(query)

    def calculate_conductance(self) -> float:
        """Возвращает среднюю проводимость сообществ."""
        query = f"""
            CALL gds.conductance.stream(
                '{self.graph_name}',
                {{ communityProperty: '{self.property_name}' }}
            )
            YIELD conductance
            RETURN AVG(conductance) AS avg_conductance
        """
        return self._get_metric(query)

    def calculate_coverage(self) -> float:
        """Возвращает среднее значение coverage по сообществам.

        Coverage определяется как отношение числа внутренних рёбер
        сообщества к общему числу рёбер, инцидентных его вершинам.
        """
        query = f"""
            MATCH (n)-[r]-(m)
            WHERE n.{self.property_name} IS NOT NULL
            WITH
                n.{self.property_name} AS community,
                CASE
                    WHEN n.{self.property_name} = m.{self.property_name}
                    THEN 1 ELSE 0
                END AS is_internal
            WITH
                community,
                sum(is_internal) AS internal_edges,
                count(r) AS total_edges
            WHERE total_edges > 0
            RETURN
                AVG(toFloat(internal_edges) / total_edges) AS avg_coverage
        """
        return self._get_metric(query)


class Leiden(CommunityDetection):
    """Алгоритм Leiden для детекции сообществ."""

    def __init__(self):
        super().__init__("leiden", "leiden_community")


class Louvain(CommunityDetection):
    """Алгоритм Louvain для детекции сообществ."""

    def __init__(self):
        super().__init__("louvain", "louvain_community")
