from app.database.neo4j_connection import Neo4jConnection
import logging
from collections import defaultdict
from math import sqrt

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

        Бросает исключение при отсутствии graph_name, пустом результате
        или ошибке выполнения запроса.
        """
        if not self.graph_name:
            raise ValueError("graph_name is not set; run detect_communities first")

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

            raise ValueError("Metric query returned empty result")

        except Exception:
            logger.exception("Error executing metric query")
            raise

    def calculate_modularity(self) -> float:
        """Возвращает значение модульности кластеризации."""
        try:
            query = (
                f"CALL gds.{self.algorithm_name}.stats('{self.graph_name}') "
                f"YIELD modularity RETURN modularity"
            )
            return self._get_metric(query)
        except Exception:
            logger.exception("Error calculating modularity")
            raise

    def calculate_conductance(self) -> float:
        """Возвращает оценку проводимости сообществ.

        Рассчитывает как отношение внешних рёбер к общему числу рёбер.
        """
        try:
            query = f"""
                MATCH (n)-[r]-(m)
                WHERE n.{self.property_name} IS NOT NULL
                WITH
                    n.{self.property_name} AS community,
                    CASE
                        WHEN n.{self.property_name} = m.{self.property_name}
                        THEN 0 ELSE 1
                    END AS is_external,
                    r
                WITH
                    community,
                    sum(is_external) AS external_edges,
                    count(r) AS total_edges
                WHERE total_edges > 0
                RETURN
                    AVG(toFloat(external_edges) / total_edges) AS avg_conductance
            """
            return self._get_metric(query)
        except Exception:
            logger.exception("Error calculating conductance")
            raise

    def calculate_coverage(self) -> float:
        """Возвращает среднее значение coverage по сообществам.

        Coverage определяется как отношение числа внутренних рёбер
        сообщества к общему числу рёбер, инцидентных его вершинам.
        """
        try:
            query = f"""
                MATCH (n)-[r]-(m)
                WHERE n.{self.property_name} IS NOT NULL
                WITH
                    n.{self.property_name} AS community,
                    CASE
                        WHEN n.{self.property_name} = m.{self.property_name}
                        THEN 1 ELSE 0
                    END AS is_internal,
                    r
                WITH
                    community,
                    sum(is_internal) AS internal_edges,
                    count(r) AS total_edges
                WHERE total_edges > 0
                RETURN
                    AVG(toFloat(internal_edges) / total_edges) AS avg_coverage
            """
            return self._get_metric(query)
        except Exception:
            logger.exception("Error calculating coverage")
            raise


class Leiden(CommunityDetection):
    """Алгоритм Leiden для детекции сообществ."""

    def __init__(self):
        super().__init__("leiden", "leiden_community")


class Louvain(CommunityDetection):
    """Алгоритм Louvain для детекции сообществ."""

    def __init__(self):
        super().__init__("louvain", "louvain_community")