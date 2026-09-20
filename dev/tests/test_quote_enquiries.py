from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _use_tmp_db(tmp_path, monkeypatch):
    # Force a temporary sqlite DB for tests.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")

    # Reload db module so engine/session bind to the new DATABASE_URL.
    import importlib
    import dev.db as db

    importlib.reload(db)

    # Ensure models are created in this fresh DB.
    import dev.models  # noqa: F401

    db.Base.metadata.create_all(bind=db.engine)

    yield


def _client():
    from dev.app import app

    app.config.update(TESTING=True)
    return app.test_client()


def test_create_quote_enquiry_json_success():
    client = _client()

    resp = client.post(
        "/api/quote-enquiries",
        json={
            "name": "Vinay",
            "mobile_number": "+91 9876543210",
            "product_category": "Files",
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "created"
    assert data["quote_id"]


def test_create_quote_enquiry_validation_error():
    client = _client()

    resp = client.post("/api/quote-enquiries", json={"name": "X"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_list_quote_enquiries():
    client = _client()

    client.post(
        "/api/quote-enquiries",
        json={
            "name": "Vinay",
            "mobile_number": "+91 9876543210",
            "product_category": "Files",
        },
    )

    resp = client.get("/api/quote-enquiries")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data
    assert len(data["items"]) >= 1
