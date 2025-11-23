"""
    Контекст для вычисления метрик сетей
"""

class MetricCalculationContext:
    def __init__(
            self,
            need_leiden_clusterization: bool = False,
            need_louvain_clusterization: bool = False,
            need_betweenness: bool = False,
            need_pagerank: bool = False,
    ):
        self.need_leiden_clusterization = need_leiden_clusterization
        self.need_louvain_clusterization = need_louvain_clusterization
        self.need_betweenness = need_betweenness
        self.need_pagerank = need_pagerank
