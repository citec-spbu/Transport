from dash import Dash, dcc, html
from AnalisisManager import AnalisisManager
from context.PrintGraphAnalisContext import PrintGraphAnalisContext
from context.AnalisisContext import AnalisContext
from context.GraphAnalisContext import GraphAnalisContext
from enums.GraphTypes import GraphTypes
from enums.HeatMapMetrics import HeatMapMetrics

app = Dash(__name__)

graph_analysis_context = GraphAnalisContext(
    city_name="Санкт-Петербург",
    graph_type=GraphTypes.BUS_GRAPH,
    print_graph_analis_context=PrintGraphAnalisContext(
        heat_map_metrics_list=[HeatMapMetrics.PAGE_RANK]
    )
)
analis_context = AnalisContext(
    ru_city_name="Санкт-Петербург",
    graph_analis_context=[graph_analysis_context]
)
manager = AnalisisManager()
figures = manager.process(analis_context)

graph_components = []
if figures:
    for i, fig in enumerate(figures):
        graph_components.append(dcc.Graph(id=f'graph-{i}', figure=fig))

app.layout = html.Div(children=[
    html.H1(children='Анализ транспортной сети'),
    html.Div(children='Отображение сгенерированных графиков:'),
    *graph_components
])

# Запуск веб-сервера
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)
