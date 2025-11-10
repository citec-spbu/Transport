"""
    Контекст для вычисления метрик сетей
"""


class MetricCalculationContext:
    def __init__(
            self,
            need_leiden_community_id: bool = True,
            need_louvain_community_id: bool = True,
            need_leiden_modularity: bool = True,
            need_louvain_modularity: bool = True,
            need_betweenness: bool = True,
            need_page_rank: bool = True,
            need_degree: bool = True
    ):
        self.need_leiden_community_id = need_leiden_community_id
        self.need_louvain_community_id = need_louvain_community_id
        self.need_leiden_modularity = need_leiden_modularity
        self.need_louvain_modularity = need_louvain_modularity
        self.need_betweenness = need_betweenness
        self.need_page_rank = need_page_rank
        self.need_degree = need_degree
