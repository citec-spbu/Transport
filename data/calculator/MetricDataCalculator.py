from context import GraphAnalisContext
from database.MetricsDistribution import DegreeDistribution, BetweennessDistribution, PageRankDistribution, \
    LeidenClusteringDistribution, LouvainClusteringDistribution

"""
    Класс вычисляющий метрики сетей(берёт уже записанные метрики из бд или вычисляет не сложные)
"""


class MetricDataCalculator:
    def __init__(
            self,
            graph_analisis_context: GraphAnalisContext
    ):
        metric_calculation_context = graph_analisis_context.metric_calculation_context
        self.degree_distribution_calculator = None
        self.betweenness_distribution_calculator = None
        self.page_rank_distribution_calculator = None
        # Initialize optional calculators to None so attributes always exist
        self.leiden_community_id_calculator = None
        self.louvain_community_id_calculator = None
        db_parameters = graph_analisis_context.neo4j_DB_graph_parameters
        if metric_calculation_context.need_degree:
            self.degree_distribution_calculator = DegreeDistribution(db_parameters)
        if metric_calculation_context.need_betweenness:
            self.betweenness_distribution_calculator = BetweennessDistribution(db_parameters)
        if metric_calculation_context.need_page_rank:
            self.page_rank_distribution_calculator = PageRankDistribution(db_parameters)
        if metric_calculation_context.need_leiden_community_id:
            self.leiden_community_id_calculator = LeidenClusteringDistribution(db_parameters)
        if metric_calculation_context.need_louvain_community_id:
            self.louvain_community_id_calculator = LouvainClusteringDistribution(db_parameters)

    def calculate_data(self, prepare_result: dict):
        if prepare_result is None:
            prepare_result = {}
        degree_distribution = {}
        if self.degree_distribution_calculator is not None:
            degree_distribution_data = self.degree_distribution_calculator.calculate_distribution()
            degree_distribution = {"degree_value": [item[1] for item in degree_distribution_data] }

        betweenness_distribution = {}
        if self.betweenness_distribution_calculator is not None:
            betweenness_distribution_data = self.betweenness_distribution_calculator.calculate_distribution()
            betweenness_distribution = {
                "betweenness_identity": [convert_to_point(item[0]) for item in betweenness_distribution_data],
                "betweenness_value": [item[1] for item in betweenness_distribution_data],
            }

        page_rank_distribution = {}
        if self.page_rank_distribution_calculator is not None:
            page_rank_distribution_data = self.page_rank_distribution_calculator.calculate_distribution()
            page_rank_distribution = {
                "page_rank_identity": [convert_to_point(item[0]) for item in page_rank_distribution_data],
                "page_rank_value": [item[1] for item in page_rank_distribution_data],
            }

        leiden_distribution = {}
        if self.leiden_community_id_calculator is not None:
            leiden_distribution_data = self.leiden_community_id_calculator.calculate_distribution()
            leiden_distribution = {
                "leiden_identity": [convert_to_point(item[0]) for item in leiden_distribution_data],
                "leiden_value": [item[1] for item in leiden_distribution_data],
            }

        louvain_distribution = {}
        if self.louvain_community_id_calculator is not None:
            louvain_distribution_data = self.louvain_community_id_calculator.calculate_distribution()
            louvain_distribution = {
                "louvain_identity": [convert_to_point(item[0]) for item in louvain_distribution_data],
                "louvain_value": [item[1] for item in louvain_distribution_data],
            }
        return {
                    **degree_distribution,
                    **betweenness_distribution,
                    **page_rank_distribution,
                    **prepare_result,
                    **louvain_distribution,
                    **leiden_distribution
                }

def convert_to_point(data):
    if not (hasattr(data, 'latitude') and hasattr(data, 'longitude')):
        parsed_point = data.split(" ")
        return Point(parsed_point[2][:-1:], parsed_point[1][1::])
    else:
        return data
class Point:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude