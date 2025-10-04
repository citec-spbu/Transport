from dash import Dash, dcc, html
from AnalisisManager import AnalisisManager
from context.AnalisisContext import AnalisContext

app = Dash(__name__)


analis_context = AnalisContext(ru_city_name="Санкт-Петербург")
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
