from app.database.neo4j_connection import Neo4jConnection
import logging

logger = logging.getLogger(__name__)

class CommunityDetection:
    """Базовый класс для детекции сообществ и расчёта метрик GDS."""
    def __init__(self, algorithm_name: str, property_name: str):
        """Инициализирует детектор сообществ.

        algorithm_name — имя алгоритма GDS (leiden/louvain),
        property_name — свойство для записи идентификатора сообщества.
        """
        self.algorithm_name = algorithm_name
        self.property_name = property_name
        self.connection = Neo4jConnection()
        self.graph_name = None

    def detect_communities(self, graph_name: str, relationship_weight_property: str) -> None:
        """Запускает алгоритм детекции сообществ для указанного графа."""
        self.graph_name = graph_name
        self._write_communities(graph_name, relationship_weight_property)

    def _write_communities(self, graph_name: str, relationship_weight_property: str) -> None:
        """Записывает метки сообществ в узлы графа."""
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
            logger.exception("Error writing communities")
            raise

    def _get_metric(self, query: str) -> float:
        """Выполняет запрос метрики и возвращает значение.

        Безопасно проверяет структуру результата и возвращает 0.0
        при любой ошибке или пустом результате.
        """
        if not self.graph_name:
            return 0.0
        try:
            result = self.connection.run(query)
            if (
                isinstance(result, (list, tuple)) and len(result) > 0 and
                isinstance(result[0], (list, tuple)) and len(result[0]) > 0 and
                result[0][0] is not None
            ):
                return float(result[0][0])
            return 0.0
        except Exception:
            logger.exception("Error executing metric query")
            return 0.0

    def calculate_modularity(self) -> float:
        """Возвращает модульность обнаруженных сообществ."""
        query = f"CALL gds.{self.algorithm_name}.stats('{self.graph_name}') YIELD modularity RETURN modularity"
        return self._get_metric(query)

    def calculate_silhouette(self) -> float:
        """Возвращает значение силуэта кластеризации."""
        query = f'''
            CALL gds.{self.algorithm_name}.stats(
                '{self.graph_name}',
                {{ computeSilhouette: true }}
            ) YIELD silhouette RETURN silhouette
        '''
        return self._get_metric(query)

    def calculate_conductance(self) -> float:
        """Возвращает среднюю проводимость сообществ."""
        query = f'''
            CALL gds.alpha.conductance.stream('{self.graph_name}')
            YIELD communityId, conductance
            RETURN AVG(conductance) AS avg_conductance
        '''
        return self._get_metric(query)

    def calculate_coverage(self) -> float:
        """Возвращает среднюю покрываемость сообществ."""
        query = f'''
            CALL gds.alpha.coverage.stream('{self.graph_name}')
            YIELD communityId, coverage
            RETURN AVG(coverage) AS avg_coverage
        '''
        return self._get_metric(query)


class Leiden(CommunityDetection):
    def __init__(self):
        """Алгоритм Leiden для детекции сообществ."""
        super().__init__("leiden", "leiden_community")


class Louvain(CommunityDetection):
    def __init__(self):
        """Алгоритм Louvain для детекции сообществ."""
        super().__init__("louvain", "louvain_community")
