from enum import Enum

import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from context.PrintGraphAnalisContext import PrintGraphAnalisContext
from context.MetricCalculationContext import MetricCalculationContext
"""
    Класс отрисовывающий графики по вычисленным метрикам 
"""


class Printer:
    def __init__(
            self,
            data,
            metric_calculation_context: MetricCalculationContext
    ):
        self.data = data
        self.metric_calculation_context = metric_calculation_context

    def print_graphics(self, print_graph_analis_context: PrintGraphAnalisContext):
        figures = []
        for hist_metric in print_graph_analis_context.histogram_map_metrics_list:
            figures.append(self.plot_histogram(hist_metric))
        for heat_map_metric in print_graph_analis_context.heat_map_metrics_list:
            figures.append(self.plot_heatmap_on_map(heat_map_metric, print_graph_analis_context.mesh_size))
        return figures


    def plot_histogram(
            self,
            metric: Enum,
            title="Distribution of metric_value ",
            ylabel="Frequency"
    ):
        metric_name = str(metric.value)
        title += metric_name
        metric_values = self.data[metric_name + "_value"]

        df = pd.DataFrame({"metric_value: " + metric_name: metric_values})

        fig = px.histogram(
            df,
            x="metric_value: " + metric_name,
            title=title,
            labels={
                "metric_value ": metric_name,
                "count": ylabel
            },
            marginal="rug"
        )

        return fig

    def plot_heatmap_on_map(
            self,
            metric: Enum,
            resolution,
            colorscale='Viridis'
    ):
        latitudes = []
        longitudes = []
        metric_values = []
        metric_name = str(metric.value)

        for item in range(len(self.data[metric_name + "_identity"])):
            try:
                parsed_point = self.data[metric_name + "_identity"][item].split(" ")
                lat, lon = parsed_point[1][1::], parsed_point[2][:-1:]
                latitudes.append(float(lat))
                longitudes.append(float(lon))
                metric_values.append(self.data[metric_name + "_value"][item])
            except Exception:
                print(f"Skipping invalid identity")

        df = pd.DataFrame({
            "latitude": latitudes,
            "longitude": longitudes,
            "metric_value": metric_values
        })
        df['metric_value'] = df['metric_value'].fillna(0)

        lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
        lon_min, lon_max = df['longitude'].min(), df['longitude'].max()

        lon_edges = np.linspace(lon_min, lon_max, resolution + 1)
        lat_edges = np.linspace(lat_min, lat_max, resolution + 1)

        lon_centers = (lon_edges[:-1] + lon_edges[1:]) / 2
        lat_centers = (lat_edges[:-1] + lat_edges[1:]) / 2

        avg_values = np.empty((resolution, resolution))
        avg_values.fill(0)

        for i in range(resolution):
            for j in range(resolution):
                mask = (
                        (df['longitude'] >= lon_edges[i]) &
                        (df['longitude'] < lon_edges[i + 1]) &
                        (df['latitude'] >= lat_edges[j]) &
                        (df['latitude'] < lat_edges[j + 1])
                )

                cell_points = df[mask]

                if len(cell_points) > 0:
                    mean_value = cell_points["metric_value"].mean()
                    avg_values[j, i] = 0 if np.isnan(mean_value) or np.isinf(mean_value) else mean_value

        fig = go.Figure()

        fig.add_trace(go.Heatmap(
            z=avg_values,
            x=lon_centers,
            y=lat_centers,
            colorscale=colorscale,
            colorbar=dict(title='Среднее значение метрики ' + metric_name),
            hoverinfo='x+y+z',
            name='Средние значения ' + metric_name,
        ))

        return fig
