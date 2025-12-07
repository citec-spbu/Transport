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
        metric_calculation_context: MetricCalculationContext = None,
        graph_name: str = "Graph",
        graph_type: GraphTypes = GraphTypes.BUS_GRAPH,
        need_prepare_data: bool = False,
        need_create_graph: bool = False,
        city_name: str = "",
        db_graph_parameters: DBGraphParameters = None
    ):
        self.metric_calculation_context = metric_calculation_context or MetricCalculationContext()
        self.db_graph_parameters = db_graph_parameters or DBGraphParameters()
        self.graph_name = graph_name
        self.graph_type = graph_type
        self.need_prepare_data = need_prepare_data
        self.need_create_graph = need_create_graph
        self.city_name = city_name

