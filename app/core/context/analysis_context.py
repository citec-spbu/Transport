import random

from app.core.context.db_graph_parameters import DBGraphParameters
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.models.graph_types import GraphTypes

"""
    Контекст для анализа сети
"""

class AnalysisContext:
    def __init__(
        self,
        metric_calculation_context: MetricCalculationContext = MetricCalculationContext(),
        graph_name: str = "SomeGraph" + str(random.random()),
        graph_type: GraphTypes = GraphTypes.BUS_GRAPH,
        need_prepare_data: bool = False,
        need_create_graph: bool = False,
        city_name: str = ""
    ):
        self.metric_calculation_context = metric_calculation_context
        self.graph_name = graph_name
        self.graph_type = graph_type
        self.need_prepare_data = need_prepare_data
        self.need_create_graph = need_create_graph
        self.db_graph_parameters = DBGraphParameters()
        self.city_name = city_name
