from app.database.neo4j_connection import Neo4jConnection

"""
    Класс содержащий query для вычисления метрик сети 
"""

class MetricsCalculate:
    def __init__(self, metric_name, write_property):
        self.metric_name = metric_name
        self.write_property = write_property
        self.connection = Neo4jConnection()

    def metric_calculate(self, graph_name, weight_property):
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
        super().__init__("betweenness", "betweenness")


class PageRank(MetricsCalculate):
    def __init__(self):
        super().__init__("pageRank", "pagerank")
