from context.AnalisisContext import AnalisContext
from data.calculator.MetricDataCalculator import MetricDataCalculator
from data.preparer.MetricDataPreparer import MetricDataPreparer
from database.AnalysPreparer import AnalysPreparer
from graphics.Printer import Printer
"""
    Класс ответственный за анализ сетей
"""


class AnalisisManager:

    def process(self, analis_context: AnalisContext):
        ru_city_name = analis_context.ru_city_name

        for graph_analis_context in analis_context.graph_analis_context:
            graph_analis_context.city_name = ru_city_name
            db_manager_constructor = graph_analis_context.graph_type.value
            db_manager = db_manager_constructor(graph_analis_context)
            analisis_preparer = AnalysPreparer(graph_analis_context)

            if graph_analis_context.need_create_graph == True:
                db_manager.update_db(ru_city_name)
            analisis_preparer.prepare()

            prepare_result = None
            if graph_analis_context.need_prepare_data:
                metric_data_preparer = MetricDataPreparer(graph_analis_context)
                prepare_result = metric_data_preparer.prepare_metrics()

            if graph_analis_context.need_calculate_and_print_data:
                metric_data_calculator = MetricDataCalculator(graph_analis_context)
                data = metric_data_calculator.calculate_data(prepare_result)

                printer = Printer(
                    data,
                    graph_analis_context.metric_calculation_context,
                )
                return printer.print_graphics(graph_analis_context.print_graph_analis_context)
