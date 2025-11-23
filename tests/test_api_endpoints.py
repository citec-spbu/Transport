import pytest
from fastapi.testclient import TestClient
from app.main import app

from app.api.v1.endpoints import datasets as datasets_mod
from app.api.v1.endpoints import auth as auth_mod
from app.api.v1.endpoints import analysis as analysis_mod
from app.core.context.analysis_context import AnalysisContext

client = TestClient(app)


def test_guest_token():
    r = client.post("/v1/auth/guest")
    assert r.status_code == 200
    data = r.json()
    assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 0


def test_request_and_verify_code(monkeypatch):
    # Подготавливаем код в модуле авторизации
    auth_mod.verification_codes["user@example.com"] = "654321"

    # Некорректный код
    r_bad = client.post("/v1/auth/verify_code", json={"email": "user@example.com", "code": "000000"})
    assert r_bad.status_code == 200
    assert r_bad.json().get("token") is None

    # Корректный код
    r = client.post("/v1/auth/verify_code", json={"email": "user@example.com", "code": "654321"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "user@example.com"
    assert data["token"] is not None


def test_upload_and_delete_dataset(monkeypatch):
    # Мокаем AnalysisManager и Neo4jConnection, чтобы не обращаться к реальной БД
    class DummyManager:
        def __init__(self, *a, **k):
            pass

        def process(self, analysis_context):
            # Убедимся, что db_graph_parameters содержит минимальные атрибуты
            dbp = analysis_context.db_graph_parameters
            dbp.main_node_name = "TestNode"
            dbp.main_rels_name = "TEST_REL"
            dbp.graph_name = analysis_context.graph_name
            return []

    class DummyConn:
        def __init__(self, *a, **k):
            pass

        def run(self, *a, **k):
            return None

        def close(self):
            return None

    monkeypatch.setattr(datasets_mod, "AnalysisManager", DummyManager)
    monkeypatch.setattr(datasets_mod, "Neo4jConnection", DummyConn)

    payload = {"transport_type": "bus", "city": "TestCity"}
    r = client.post("/v1/datasets/", json=payload)
    assert r.status_code == 200
    resp = r.json()
    assert "dataset_id" in resp
    dsid = resp["dataset_id"]

    # Теперь проверим, что датасет сохранён в active_datasets
    assert dsid in datasets_mod.active_datasets

    # Удаляем датасет
    r2 = client.delete(f"/v1/datasets/{dsid}")
    assert r2.status_code == 200
    assert dsid not in datasets_mod.active_datasets


def test_cluster_and_metric_endpoints(monkeypatch):
    # Подготавливаем контекст и добавляем в active_datasets
    ctx = AnalysisContext()
    dbp = ctx.db_graph_parameters
    dbp.main_node_name = "TestNode"
    dbp.main_rels_name = "TEST_REL"
    dbp.graph_name = ctx.graph_name

    dsid = "test-ds-1"
    datasets_mod.active_datasets[dsid] = {"id": dsid, "name": "x", "analysis_context": ctx}

    # Мокаем AnalysisManager внутри модуля analysis (этот импорт отдельный)
    class DummyManagerForAnalysis:
        def __init__(self, *a, **k):
            pass

        def process(self, analysis_context):
            # В зависимости от настроек metric_calculation_context вернём разный формат
            mctx = analysis_context.metric_calculation_context
            if mctx.need_leiden_clusterization or mctx.need_louvain_clusterization:
                return [{"id": "n1", "name": "Node1", "cluster_id": 0, "coordinates": [30.0, 60.0]}]
            else:
                return [{"id": "n1", "name": "Node1", "metric": 1.23, "coordinates": [30.0, 60.0]}]

    monkeypatch.setattr(analysis_mod, "AnalysisManager", DummyManagerForAnalysis)

    # Тест кластеризации
    r = client.post("/v1/analysis/cluster", json={"dataset_id": dsid, "method": "leiden"})
    assert r.status_code == 200
    data = r.json()
    assert data["dataset_id"] == dsid
    assert isinstance(data.get("nodes"), list) and len(data["nodes"]) == 1
    assert data["nodes"][0]["id"] == "n1"

    # Тест метрики
    r2 = client.post("/v1/analysis/metric", json={"dataset_id": dsid, "metric": "pagerank"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["dataset_id"] == dsid
    assert isinstance(d2.get("nodes"), list) and len(d2["nodes"]) == 1
    assert d2["nodes"][0]["metric"] == 1.23

    # Cleanup
    datasets_mod.active_datasets.pop(dsid, None)
