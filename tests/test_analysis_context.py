import pytest
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.context.db_graph_parameters import DBGraphParameters
from app.models.graph_types import GraphTypes


def test_default_initialization():
    ctx = AnalysisContext()
    assert isinstance(ctx.metric_calculation_context, MetricCalculationContext)
    assert isinstance(ctx.db_graph_parameters, DBGraphParameters)
    assert ctx.graph_name == "Graph"
    assert ctx.graph_type == GraphTypes.BUS_GRAPH
    assert ctx.need_prepare_data is False
    assert ctx.need_create_graph is False
    assert ctx.city_name == ""


def test_behavior_with_partial_parameters():
    mc = MetricCalculationContext(need_pagerank=True)
    dbp = DBGraphParameters()
    dbp.main_node_name = 'Stop'

    ctx = AnalysisContext(
        graph_name='CustomGraph',
        need_prepare_data=True,
        metric_calculation_context=mc,
        db_graph_parameters=dbp,
        city_name='Town',
    )

    assert ctx.graph_name == 'CustomGraph'
    assert ctx.need_prepare_data is True
    assert ctx.metric_calculation_context.need_pagerank is True
    assert ctx.db_graph_parameters.main_node_name == 'Stop'
    assert ctx.city_name == 'Town'


def test_metric_calculation_context_flags_default_and_set():
    mc_default = MetricCalculationContext()
    assert mc_default.need_leiden_clusterization is False
    assert mc_default.need_louvain_clusterization is False
    assert mc_default.need_betweenness is False
    assert mc_default.need_pagerank is False

    mc = MetricCalculationContext(
        need_leiden_clusterization=True,
        need_louvain_clusterization=True,
        need_betweenness=True,
        need_pagerank=True,
    )
    assert mc.need_leiden_clusterization is True
    assert mc.need_louvain_clusterization is True
    assert mc.need_betweenness is True
    assert mc.need_pagerank is True


def test_nested_contexts_are_isolated_by_default():
    a = AnalysisContext()
    b = AnalysisContext()

    # объекты должны быть независимы
    assert a.metric_calculation_context is not b.metric_calculation_context
    assert a.db_graph_parameters is not b.db_graph_parameters

    # изменения одного не влияют на другой
    a.metric_calculation_context.need_pagerank = True
    assert b.metric_calculation_context.need_pagerank is False
    a.db_graph_parameters.main_node_name = 'X'
    assert b.db_graph_parameters.main_node_name is None


def test_nested_contexts_with_explicit_instances_are_isolated():
    mc1 = MetricCalculationContext()
    mc2 = MetricCalculationContext()
    db1 = DBGraphParameters()
    db2 = DBGraphParameters()

    c1 = AnalysisContext(metric_calculation_context=mc1, db_graph_parameters=db1)
    c2 = AnalysisContext(metric_calculation_context=mc2, db_graph_parameters=db2)

    c1.metric_calculation_context.need_betweenness = True
    assert c2.metric_calculation_context.need_betweenness is False

    c1.db_graph_parameters.city_name = 'C1'
    assert c2.db_graph_parameters.city_name is None
