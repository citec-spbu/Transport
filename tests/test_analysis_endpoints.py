import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.endpoints import datasets as datasets_mod
from app.api.v1.endpoints import analysis as analysis_mod
from app.core.context.analysis_context import AnalysisContext

pytestmark = pytest.mark.integration

client = TestClient(app)


# -----------------------------
# Хелпер для создания dataset
# -----------------------------
def _prepare_dataset(dsid="ds-1"):
    ctx = AnalysisContext()
    dbp = ctx.db_graph_parameters
    dbp.main_node_name = "MN"
    dbp.main_rels_name = "MR"
    dbp.graph_name = ctx.graph_name

    datasets_mod.active_datasets[dsid] = {"id": dsid, "name": "n", "analysis_context": ctx}
    return dsid


# -----------------------------
# Happy path: кластеризация
# -----------------------------
@pytest.mark.parametrize("method,cluster_id", [("leiden", 2), ("louvain", 5)])
def test_cluster_success(monkeypatch, method, cluster_id):
    dsid = _prepare_dataset(f"ds-cl-{method}")

    class DummyManager:
        def __init__(self, *a, **k): pass
        def process(self, analysis_context):
            return [{"id": "n1", "name": "Node1", "cluster_id": cluster_id, "coordinates": [30.0, 60.0]}]

    monkeypatch.setattr(analysis_mod, "AnalysisManager", DummyManager)

    r = client.post("/v1/analysis/cluster", json={"dataset_id": dsid, "method": method})
    assert r.status_code == 200
    data = r.json()
    node = data["nodes"][0]
    assert node["id"] == "n1"
    assert node["coordinates"] == [30.0, 60.0]
    assert node["cluster_id"] == cluster_id
    # лишних полей нет
    assert set(node.keys()) <= {"id", "name", "cluster_id", "coordinates"}

    datasets_mod.active_datasets.pop(dsid, None)


# -----------------------------
# Happy path: метрики
# -----------------------------
@pytest.mark.parametrize("metric_name,value", [("pagerank", 3.14), ("betweenness", 2.5)])
def test_metric_success(monkeypatch, metric_name, value):
    dsid = _prepare_dataset(f"ds-m-{metric_name}")

    class DummyManager:
        def __init__(self, *a, **k): pass
        def process(self, analysis_context):
            return [{"id": "m1", "name": "NodeM", "metric": value, "coordinates": [31.0, 61.0]}]

    monkeypatch.setattr(analysis_mod, "AnalysisManager", DummyManager)

    r = client.post("/v1/analysis/metric", json={"dataset_id": dsid, "metric": metric_name})
    assert r.status_code == 200
    node = r.json()["nodes"][0]
    assert node["id"] == "m1"
    assert node["coordinates"] == [31.0, 61.0]
    assert node["metric"] == value
    # лишних полей нет
    assert set(node.keys()) <= {"id", "name", "metric", "coordinates"}

    datasets_mod.active_datasets.pop(dsid, None)


# -----------------------------
# Dataset не найден
# -----------------------------
@pytest.mark.parametrize("endpoint,payload", [
    ("/v1/analysis/cluster", {"dataset_id": "no-ds-cl", "method": "leiden"}),
    ("/v1/analysis/metric", {"dataset_id": "no-ds-m", "metric": "pagerank"}),
])
def test_dataset_not_found(endpoint, payload):
    r = client.post(endpoint, json=payload)
    assert r.status_code == 404
    assert r.json()["detail"] == "Dataset not found"


# -----------------------------
# Некорректный метод или метрика
# -----------------------------
@pytest.mark.parametrize("payload", [
    {"dataset_id": _prepare_dataset("ds-cl-bad"), "method": "unknown"},
    {"dataset_id": _prepare_dataset("ds-m-bad"), "metric": "unknown_metric"}
])
def test_invalid_method_or_metric(payload):
    r = client.post("/v1/analysis/cluster" if "method" in payload else "/v1/analysis/metric", json=payload)
    assert r.status_code == 422
    # очистка
    datasets_mod.active_datasets.pop(payload["dataset_id"], None)


# -----------------------------
# Пустой список узлов
# -----------------------------
@pytest.mark.parametrize("endpoint,payload", [
    ("/v1/analysis/cluster", {"dataset_id": _prepare_dataset("ds-cl-empty"), "method": "leiden"}),
    ("/v1/analysis/metric", {"dataset_id": _prepare_dataset("ds-m-empty"), "metric": "pagerank"}),
])
def test_empty_nodes(monkeypatch, endpoint, payload):
    class DummyManager:
        def __init__(self, *a, **k): pass
        def process(self, ctx): return []

    monkeypatch.setattr(analysis_mod, "AnalysisManager", DummyManager)

    r = client.post(endpoint, json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["nodes"] == []

    datasets_mod.active_datasets.pop(payload["dataset_id"], None)


# -----------------------------
# Исключения AnalysisManager → 502
# -----------------------------
@pytest.mark.parametrize("endpoint,payload", [
    ("/v1/analysis/cluster", {"dataset_id": _prepare_dataset("ds-cl-err"), "method": "leiden"}),
    ("/v1/analysis/metric", {"dataset_id": _prepare_dataset("ds-m-err"), "metric": "pagerank"}),
])
def test_analysis_manager_exception(monkeypatch, endpoint, payload):
    class BadManager:
        def __init__(self, *a, **k): pass
        def process(self, ctx): raise RuntimeError("boom")

    monkeypatch.setattr(analysis_mod, "AnalysisManager", BadManager)

    r = client.post(endpoint, json=payload)
    assert r.status_code == 502
    assert "External service error" in r.json()["detail"]

    datasets_mod.active_datasets.pop(payload["dataset_id"], None)


# -----------------------------
# Ошибки параметров (отсутствует dataset_id, пустой metric/method)
# -----------------------------
@pytest.mark.parametrize("endpoint,payload", [
    # dataset_id отсутствует
    ("/v1/analysis/cluster", {"method": "leiden"}),
    ("/v1/analysis/metric", {"metric": "pagerank"}),

    # метод/метрика отсутствует
    ("/v1/analysis/cluster", {"dataset_id": "ds-cl-1"}), 
    ("/v1/analysis/metric", {"dataset_id": "ds-m-1"}), 
])
def test_missing_required_params(endpoint, payload):
    r = client.post(endpoint, json=payload)
    assert r.status_code == 422
