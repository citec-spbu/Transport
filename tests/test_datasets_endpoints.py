import pytest
from fastapi.testclient import TestClient
import copy

from app.main import app
from app.api.v1.endpoints import datasets as datasets_mod
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext

pytestmark = pytest.mark.integration

client = TestClient(app)


# -----------------------------
# Хелперы для моков
# -----------------------------
class DummyManager:
    """Менеджер, который просто заполняет db_graph_parameters и возвращает пустой список."""
    def __init__(self, *a, **k):
        pass

    def process(self, analysis_context):
        dbp = analysis_context.db_graph_parameters
        dbp.main_node_name = "TestNode"
        dbp.main_rels_name = "TEST_REL"
        dbp.graph_name = analysis_context.graph_name
        return []


class SpyConn:
    """Spy для Neo4jConnection, отслеживает run и close вызовы."""
    def __init__(self, *a, **k):
        self.runs = 0
        self.closed = False

    def run(self, *a, **k):
        self.runs += 1

    def close(self):
        self.closed = True


class BadConn:
    """Мокаем падение при run для теста исключений"""
    def __init__(self, *a, **k):
        pass

    def run(self, *a, **k):
        raise RuntimeError("Neo4j failure")

    def close(self):
        pass


# -----------------------------
# Контекстные хелперы
# -----------------------------
def make_context_primary_only():
    ctx = AnalysisContext()
    dbp = ctx.db_graph_parameters
    dbp.main_node_name = "MN"
    dbp.main_rels_name = "MR"
    dbp.graph_name = "G1"
    return ctx

def make_context_with_secondary():
    ctx = make_context_primary_only()
    dbp = ctx.db_graph_parameters
    dbp.secondary_node_name = "SN"
    dbp.secondary_rels_name = "SR"
    return ctx


# -----------------------------
# Тесты Upload
# -----------------------------
def test_upload_dataset_success(monkeypatch):
    monkeypatch.setattr(datasets_mod, "AnalysisManager", DummyManager)
    monkeypatch.setattr(datasets_mod, "Neo4jConnection", SpyConn)

    payload = {"transport_type": "bus", "city": "CityX"}
    r = client.post("/v1/datasets/", json=payload)
    assert r.status_code == 200
    dsid = r.json()["dataset_id"]
    assert dsid in datasets_mod.active_datasets

    # Clean up
    datasets_mod.active_datasets.pop(dsid, None)


@pytest.mark.parametrize("payload", [
    {"city": "CityOnly"},           # нет transport_type
    {"transport_type": "bus"},      # нет city
    {},                              # пустой
    {"transport_type": "", "city": ""},         # пустые строки
    {"transport_type": "plane", "city": "X"},   # неизвестный транспорт
])
def test_upload_invalid_payload_validation_error(payload):
    r = client.post("/v1/datasets/", json=payload)
    assert r.status_code == 422


def test_upload_manager_exception(monkeypatch):
    class BadManager:
        def __init__(self, *a, **k): pass
        def process(self, ctx): raise RuntimeError("boom")

    monkeypatch.setattr(datasets_mod, "AnalysisManager", BadManager)
    payload = {"transport_type": "bus", "city": "CityErr"}
    r = client.post("/v1/datasets/", json=payload)
    assert r.status_code == 500
    assert "Failed to create dataset" in r.json().get("detail", "")


# -----------------------------
# Тесты Delete
# -----------------------------
def test_delete_dataset_success(monkeypatch):
    monkeypatch.setattr(datasets_mod, "Neo4jConnection", SpyConn)
    ctx = make_context_primary_only()
    dsid = "ds-del-1"
    datasets_mod.active_datasets[dsid] = {"id": dsid, "name": "n", "analysis_context": ctx}

    r = client.delete(f"/v1/datasets/{dsid}")
    assert r.status_code == 200
    assert dsid not in datasets_mod.active_datasets


def test_delete_dataset_not_found():
    datasets_mod.active_datasets.pop("non-existent", None)
    r = client.delete("/v1/datasets/non-existent")
    assert r.status_code == 404
    assert "Dataset not found" in r.json().get("detail", "")


def test_delete_dataset_with_secondary_nodes(monkeypatch):
    ctx = make_context_with_secondary()
    dsid = "ds-del-2"
    datasets_mod.active_datasets[dsid] = {"id": dsid, "name": "n", "analysis_context": ctx}

    spy = SpyConn()
    monkeypatch.setattr(datasets_mod, "Neo4jConnection", lambda *a, **k: spy)

    r = client.delete(f"/v1/datasets/{dsid}")
    assert r.status_code == 200
    assert dsid not in datasets_mod.active_datasets
    assert spy.closed is True
    assert spy.runs >= 1


def test_delete_dataset_neo4j_failure(monkeypatch):
    ctx = make_context_primary_only()
    dsid = "ds-del-3"
    datasets_mod.active_datasets[dsid] = {"id": dsid, "name": "n", "analysis_context": ctx}

    monkeypatch.setattr(datasets_mod, "Neo4jConnection", BadConn)
    r = client.delete(f"/v1/datasets/{dsid}")
    assert r.status_code == 500
    assert "Failed to delete dataset" in r.json().get("detail", "")

    # Clean up
    datasets_mod.active_datasets.pop(dsid, None)


# -----------------------------
# Тесты дубликатов и повторного удаления
# -----------------------------
def test_upload_duplicate_dataset(monkeypatch):
    monkeypatch.setattr(datasets_mod, "AnalysisManager", DummyManager)
    monkeypatch.setattr(datasets_mod, "Neo4jConnection", SpyConn)

    payload = {"transport_type": "bus", "city": "CityDup"}
    r1 = client.post("/v1/datasets/", json=payload)
    dsid = r1.json()["dataset_id"]

    # Попытка повторной загрузки с тем же payload (дубликат)
    r2 = client.post("/v1/datasets/", json=payload)
    assert r2.status_code == 200

    # Clean up
    datasets_mod.active_datasets.pop(dsid, None)


def test_delete_dataset_twice(monkeypatch):
    ctx = make_context_primary_only()
    dsid = "ds-del-twice"
    datasets_mod.active_datasets[dsid] = {"id": dsid, "name": "n", "analysis_context": ctx}
    monkeypatch.setattr(datasets_mod, "Neo4jConnection", SpyConn)

    r1 = client.delete(f"/v1/datasets/{dsid}")
    assert r1.status_code == 200

    r2 = client.delete(f"/v1/datasets/{dsid}")
    assert r2.status_code == 404
