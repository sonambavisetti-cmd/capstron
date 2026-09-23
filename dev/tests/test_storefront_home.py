from fastapi.testclient import TestClient

from dev.app.main import app


def test_home_renders_storefront_template() -> None:
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Browse products" in resp.text
    assert "href=\"/products\"" in resp.text
