from app.database.neo4j_connection import Neo4jConnection

"""
    Класс содержащий query для вычисления метрик сети 
"""

class MetricsCalculate:
    """Базовый класс для запуска вычисления метрик GDS."""
    def __init__(self, metric_name, write_property):
        """Инициализирует калькулятор метрики.

        metric_name — имя процедуры GDS,
        write_property — свойство записи значения метрики.
        """
        self.metric_name = metric_name
        self.write_property = write_property
        self.connection = Neo4jConnection()

    def metric_calculate(self, graph_name, weight_property):
        """Выполняет запись метрики в узлы графа."""
        query = f'''
            CALL gds.{self.metric_name}.write(
                '{graph_name}',
                {{
                    relationshipWeightProperty: '{weight_property}',
                    writeProperty: '{self.write_property}'
                }}
            )
        '''
        return self.connection.run(query)


class Betweenness(MetricsCalculate):
    def __init__(self):
        """Калькулятор метрики промежуточности (Betweenness)."""
        super().__init__("betweenness", "betweenness")


class PageRank(MetricsCalculate):
    def __init__(self):
        """Калькулятор метрики PageRank."""
        super().__init__("pageRank", "pagerank")
