from enum import Enum
"""
    Список метрик с названиями для отрисовки в Heat Map
"""


class HeatMapMetrics(Enum):
    PAGE_RANK = 'page_rank'
    BETWEENNESS = 'betweenness'
