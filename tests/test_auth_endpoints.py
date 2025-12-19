import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.endpoints import auth as auth_mod

client = TestClient(app)


def test_guest_token_returns_token():
    r = client.post("/v1/auth/guest")
    assert r.status_code == 200
    data = r.json()
    assert "token" in data and isinstance(data["token"], str) and len(data["token"]) > 0


def test_request_code_stores_verification_code(monkeypatch):
    # изолируем словарь verification_codes
    codes = {}
    monkeypatch.setattr(auth_mod, "verification_codes", codes)

    r = client.post("/v1/auth/request_code", json={"email": "foo@example.com"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("message") == "Verification code sent"
    assert "foo@example.com" in codes


def test_verify_code_incorrect_and_correct(monkeypatch):
    # изолируем словарь verification_codes
    codes = {}
    monkeypatch.setattr(auth_mod, "verification_codes", codes)

    # устанавливаем известный код
    codes["bar@example.com"] = "111111"

    # некорректный код
    r_bad = client.post("/v1/auth/verify_code", json={"email": "bar@example.com", "code": "000000"})
    assert r_bad.status_code == 200
    assert r_bad.json().get("token") is None

    # корректный код
    r_ok = client.post("/v1/auth/verify_code", json={"email": "bar@example.com", "code": "111111"})
    assert r_ok.status_code == 200
    d = r_ok.json()
    assert d.get("email") == "bar@example.com"
    assert d.get("token") is not None