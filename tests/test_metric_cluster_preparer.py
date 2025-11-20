from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.metric_cluster.metric_cluster_preparer import MetricClusterPreparer
from app.database import neo4j_connection


def test_load_nodes_with_metrics_formats_rows(monkeypatch):
    # prepare a fake read_all that returns rows as dicts from Neo4j
    sample_rows = [
        {
            'id': '100',
            'name': 'StopA',
            'lon': 30.123,
            'lat': 59.987,
            'leiden_community': 1,
            'louvain_community': None,
            'betweenness': None,
            'pagerank': 0.123
        }
    ]

    def fake_read_all(self, query, parameters=None):
        # ensure query requested proper fields
        assert 'n.location.longitude AS lon' in query or 'location.longitude' in query
        return sample_rows

    monkeypatch.setattr(neo4j_connection.Neo4jConnection, 'read_all', fake_read_all)

    # build AnalysisContext with no metric calculation flags (we'll call loader directly)
    mc = MetricCalculationContext()
    ctx = AnalysisContext(metric_calculation_context=mc)
    # set db graph params expected
    ctx.db_graph_parameters.main_node_name = 'TestNode'

    preparer = MetricClusterPreparer(ctx)

    nodes = preparer._load_nodes_with_metrics()

    assert isinstance(nodes, list)
    assert len(nodes) == 1
    node = nodes[0]
    assert node['id'] == '100'
    assert node['name'] == 'StopA'
    assert node['coordinates'] == [30.123, 59.987]
    # pagerank should be present only if metric flag is set; loader includes pagerank field
    assert 'metric' not in node
