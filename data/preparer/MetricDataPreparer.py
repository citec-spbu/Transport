import random

from context import GraphAnalisContext
from context.MetricCalculationContext import MetricCalculationContext
from database.CommunityDetection import Leiden, Louvain
from database.GraphDbManager import GraphDBManager
from database.MetricsCalculate import Betweenness, PageRank
"""
    Класс записывающий метрики сетей в бд
"""


class MetricDataPreparer:
    def __init__(self, graph_analisis_context: GraphAnalisContext):
        self.leiden_calculator = None
        self.louvain_calculator = None
        self.betweenness_calculator = None
        self.page_rank_calculator = None
        metric_calculation_context = graph_analisis_context.metric_calculation_context
        if metric_calculation_context.need_leiden_community_id or metric_calculation_context.need_leiden_modularity:
            self.leiden_calculator = Leiden()
        if metric_calculation_context.need_louvain_community_id or metric_calculation_context.need_louvain_modularity:
            self.louvain_calculator = Louvain()
        if metric_calculation_context.need_betweenness:
            self.betweenness_calculator = Betweenness()
        if metric_calculation_context.need_page_rank:
            self.page_rank_calculator = PageRank()
        self.graph_analisis_context = graph_analisis_context

    def prepare_metrics(self):
        result = {}
        if self.leiden_calculator is not None:
            result["leiden_modularity_value"] = self.prepare_leiden()
        if self.louvain_calculator is not None:
            result["louvain_modularity_value"] = self.prepare_louvain()
        if self.betweenness_calculator is not None:
            self.prepare_betweenness()
        if self.page_rank_calculator is not None:
            self.prepare_page_rank()
        return result

    def prepare_leiden(self):
        result = self.leiden_calculator.detect_communities(
            self.graph_analisis_context.graph_name,
            self.graph_analisis_context.neo4j_DB_graph_parameters.weight
        )
        print(result)
        print(f"LeidenAlgorithm Community detection for graph {self.graph_analisis_context.graph_name} completed.")
        return result

    def prepare_louvain(self):
        result = self.louvain_calculator.detect_communities(
            self.graph_analisis_context.graph_name,
            self.graph_analisis_context.neo4j_DB_graph_parameters.weight
        )
        print(result)
        print(f"LouvainAlgorithm Community detection for graph {self.graph_analisis_context.graph_name} completed.")
        return result

    def prepare_betweenness(self):
        self.betweenness_calculator.metric_calculate(
            self.graph_analisis_context.graph_name,
            self.graph_analisis_context.neo4j_DB_graph_parameters.weight
        )
        print(f"betweenness metric calculated for graph {self.graph_analisis_context.graph_name}.")

    def prepare_page_rank(self):
        self.page_rank_calculator.metric_calculate(
            self.graph_analisis_context.graph_name,
            self.graph_analisis_context.neo4j_DB_graph_parameters.weight
        )
        print(f"pageRank metric calculated for graph {self.graph_analisis_context.graph_name}.")

