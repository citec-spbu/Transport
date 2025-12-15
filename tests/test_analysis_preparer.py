import pytest
from app.core.services.analysis_preparer import AnalysisPreparer
from app.core.context.analysis_context import AnalysisContext
from app.database import neo4j_connection


def make_ctx():
    ctx = AnalysisContext()
    dbp = ctx.db_graph_parameters
    dbp.main_node_name = "MN"
    dbp.main_rels_name = "MR"
    dbp.weight = "w"
    ctx.graph_name = "GraphUnit"
    return ctx


def test_prepare_sets_normalized_weight_and_projects(monkeypatch):
    queries = []

    def fake_run(self, query, parameters=None):
        queries.append(query)
        return []

    monkeypatch.setattr(neo4j_connection.Neo4jConnection, "run", fake_run)

    ctx = make_ctx()
    AnalysisPreparer(ctx).prepare()

    # вес должен быть нормализован
    assert ctx.db_graph_parameters.weight == "norm_w"
    # были вызваны запросы нормализации и проекции
    assert any("SET r.norm_w" in q for q in queries)
    assert any("gds.graph.project" in q for q in queries)


def test_prepare_raises_when_graph_params_missing(monkeypatch):
    ctx = make_ctx()
    ctx.db_graph_parameters.main_node_name = None

    with pytest.raises(ValueError):
        AnalysisPreparer(ctx).prepare()


def test_prepare_handles_query_exceptions(monkeypatch):
    calls = {"run": 0}

    def bad_then_bad(self, query, parameters=None):
        calls["run"] += 1
        raise RuntimeError("Neo4j error")

    monkeypatch.setattr(neo4j_connection.Neo4jConnection, "run", bad_then_bad)

    ctx = make_ctx()
    # Не должно выбрасывать, так как оба исключения перехватываются и логируются print'ами
    AnalysisPreparer(ctx).prepare()

    # нормализация веса произошла даже при ошибках
    assert ctx.db_graph_parameters.weight == "norm_w"
