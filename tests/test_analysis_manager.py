import pytest
from app.core.services.analysis_manager import AnalysisManager
from app.core.services import analysis_manager as am_mod
from app.core.services import analysis_preparer as ap_mod
from app.core.metric_cluster import metric_cluster_preparer as mcp_mod
from app.core.context.analysis_context import AnalysisContext


def make_ctx():
    ctx = AnalysisContext()
    ctx.city_name = "CityX"
    dbp = ctx.db_graph_parameters
    dbp.main_node_name = "MN"
    dbp.main_rels_name = "MR"
    dbp.weight = "w"
    return ctx


def test_process_create_and_prepare(monkeypatch):
    calls = {"update_db": 0, "prepare": 0, "prepare_metrics": 0}

    class FakeDBMgr:
        def __init__(self, ctx):
            self.ctx = ctx
        def update_db(self, city):
            calls["update_db"] += 1
            assert city == "CityX"

    # подменяем граф-тип на фиктивный класс с update_db
    ctx = make_ctx()
    ctx.graph_type = type("FakeEnum", (), {"value": FakeDBMgr})
    ctx.need_create_graph = True
    ctx.need_prepare_data = True

    def fake_prepare(self):
        calls["prepare"] += 1

    def fake_prepare_metrics(self):
        calls["prepare_metrics"] += 1
        return {"nodes": [{"id": "n1", "name": "N1", "coordinates": [30.0, 60.0]}]}

    monkeypatch.setattr(ap_mod.AnalysisPreparer, "prepare", fake_prepare)
    monkeypatch.setattr(mcp_mod.MetricClusterPreparer, "prepare_metrics", fake_prepare_metrics)

    result = AnalysisManager().process(ctx)

    assert calls["update_db"] == 1
    assert calls["prepare"] == 1
    assert calls["prepare_metrics"] == 1
    assert "nodes" in result


def test_process_only_create(monkeypatch):
    calls = {"update_db": 0}

    class FakeDBMgr:
        def __init__(self, ctx):
            pass
        def update_db(self, city):
            calls["update_db"] += 1

    ctx = make_ctx()
    ctx.graph_type = type("FakeEnum", (), {"value": FakeDBMgr})
    ctx.need_create_graph = True
    ctx.need_prepare_data = False

    result = AnalysisManager().process(ctx)

    assert calls["update_db"] == 1
    assert result is None


def test_process_only_prepare(monkeypatch):
    calls = {"prepare": 0, "prepare_metrics": 0}

    def fake_prepare(self):
        calls["prepare"] += 1

    def fake_prepare_metrics(self):
        calls["prepare_metrics"] += 1
        return {"nodes": []}

    ctx = make_ctx()
    ctx.need_create_graph = False
    ctx.need_prepare_data = True

    monkeypatch.setattr(ap_mod.AnalysisPreparer, "prepare", fake_prepare)
    monkeypatch.setattr(mcp_mod.MetricClusterPreparer, "prepare_metrics", fake_prepare_metrics)

    result = AnalysisManager().process(ctx)

    assert calls["prepare"] == 1
    assert calls["prepare_metrics"] == 1
    assert result == {"nodes": []}


def test_process_none():
    ctx = make_ctx()
    ctx.need_create_graph = False
    ctx.need_prepare_data = False

    result = AnalysisManager().process(ctx)
    assert result is None
