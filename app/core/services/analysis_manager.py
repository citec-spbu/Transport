from app.core.context.analysis_context import AnalysisContext
from app.core.metric_cluster.metric_cluster_preparer import MetricClusterPreparer
from app.core.services.analysis_preparer import AnalysisPreparer

"""
    Класс, ответственный за создание графа и проведение анализа на основе переданного контекста.
"""

class AnalysisManager:

    def process(self, analysis_context: AnalysisContext):
    """Создаёт/обновляет граф и запускает анализ.

    В зависимости от флагов в `analysis_context` строит граф
    в БД, подготавливает данные и рассчитывает метрики/кластеры.
    Возвращает результаты расчётов при необходимости.
    """

        if analysis_context.need_create_graph:
            ru_city_name = analysis_context.city_name
            db_manager_constructor = analysis_context.graph_type.value
            db_manager = db_manager_constructor(analysis_context)

            db_manager.update_db(ru_city_name)

        if analysis_context.need_prepare_data:
            analysis_preparer = AnalysisPreparer(analysis_context)
            analysis_preparer.prepare()

            metric_data_preparer = MetricClusterPreparer(analysis_context)
            return metric_data_preparer.prepare_metrics()
            
