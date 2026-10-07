import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    # Ensure env is set BEFORE importing app so startup seed uses it.
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "adminpass")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    from dev.app.main import app

    return TestClient(app)


def test_admin_login_issues_bearer_token(client: TestClient):
    res = client.post("/api/admin/login", json={"username": "admin", "password": "adminpass"})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["expires_in"] == 7 * 24 * 60 * 60


def test_admin_endpoints_require_bearer_token(client: TestClient):
    # No Authorization header
    res = client.get("/api/admin/orders")
    assert res.status_code == 401

    # Login -> token -> access protected endpoint
    login = client.post("/api/admin/login", json={"username": "admin", "password": "adminpass"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    res2 = client.get("/api/admin/orders", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
