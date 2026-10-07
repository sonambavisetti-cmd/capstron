"""VNK-2 product search/filter tests (service + Flask API). Uses in-memory SQLite only."""
from __future__ import annotations

import importlib.util
import os
from decimal import Decimal
from pathlib import Path

import pytest
from flask import Flask
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from dev.models import Base, Product, ProductCustomization, ProductSize
from dev.services.product_search import ProductSearchService, SearchValidationError

REPO = Path(__file__).resolve().parents[2]


def _add(session, sku, name, material, category="Files", spec="", sizes=(), custom=(), active=True):
    p = Product(sku=sku, name=name, description=spec, unit_price=Decimal("10.00"), quantity_available=5,
                is_active=active, category=category, material=material, specifications=spec)
    for s in sizes:
        p.sizes.append(ProductSize(size=s))
    for c in custom:
        p.customizations.append(ProductCustomization(option=c))
    session.add(p)
    return p


@pytest.fixture()
def SessionFactory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, future=True)
    with Session() as s:
        # F-01 fixture: 'PVC' only in material
        _add(s, "T-CLEAR", "Clear File Folder", "PVC", spec="Transparent cover", sizes=["A4", "A3"], custom=["LOGO PRINT"])
        _add(s, "T-DOC", "Document File", "PVC", spec="Zip closure", sizes=["A4", "FS"])
        _add(s, "T-EXP", "Expanding File", "PVC", spec="13 pockets", sizes=["FS"])
        _add(s, "T-PPFILE", "Poly Ring File", "PP", spec="D-ring", sizes=["A4"], custom=["COLOR"])
        _add(s, "T-BOX", "Archive Box", "BOARD", category="Boxes", spec="Lever arch", sizes=["A4", "A5"], custom=["LOGO PRINT"])
        _add(s, "T-PCT", "Discount 100% Pad", "BOARD", category="Stationery", spec="a_b pad", sizes=["A5"])
        _add(s, "T-OLD", "Old PVC File", "PVC", spec="gone", sizes=["A4"], active=False)
        s.commit()
    yield Session
    engine.dispose()


@pytest.fixture()
def svc(SessionFactory):
    with SessionFactory() as s:
        yield ProductSearchService(s)


def names(result):
    return [p.name for p in result.items]


# ---- service -------------------------------------------------------------
def test_f01_pvc_file_matches_material_only_product(svc):
    r = svc.search(q="PVC File")
    assert "Clear File Folder" in names(r)  # 'PVC' only in material
    assert "Poly Ring File" not in names(r)  # PP file lacks PVC
    assert "Archive Box" not in names(r)


def test_inactive_excluded(svc):
    assert "Old PVC File" not in names(svc.search(q="PVC File"))
    assert svc.search(q="gone").total == 0  # spec text of the inactive row


def test_material_filter_case_insensitive(svc):
    r = svc.search(material="pvc")
    assert r.total == 3 and all(p.material == "PVC" for p in r.items)
    assert r.applied["material"] == "PVC"


def test_size_filter_and_no_duplicates(svc):
    r = svc.search(size="A4")
    assert sorted(names(r)) == sorted(set(names(r)))
    assert set(names(r)) == {"Clear File Folder", "Document File", "Poly Ring File", "Archive Box"}
    assert svc.search(size="a4").total == 4  # normalized


def test_size_not_text_searched(svc):
    # 'A5' appears only in product_sizes for these rows (not in sku/name/spec)
    assert svc.search(q="A5").total == 0


def test_combined_ac4(svc):
    r = svc.search(q="PVC File", material="PVC", size="A4")
    assert set(names(r)) == {"Clear File Folder", "Document File"}


def test_customization_filter(svc):
    r = svc.search(customization="logo print")
    assert set(names(r)) == {"Clear File Folder", "Archive Box"}


def test_category_filter_exact_case_insensitive(svc):
    assert names(svc.search(category="boxes")) == ["Archive Box"]


def test_zero_results(svc):
    r = svc.search(q="zzzznonexistent")
    assert r.total == 0 and r.items == []


def test_wildcards_literal(svc):
    assert names(svc.search(q="%")) == ["Discount 100% Pad"]
    assert names(svc.search(q="a_b")) == ["Discount 100% Pad"]
    assert svc.search(q="_").total == 1  # only the 'a_b' spec has a literal underscore
    assert svc.search(q="\\").total == 0


def test_case_insensitive_and_multi_term_and(svc):
    assert svc.search(q="pvc FILE").total == 3
    assert svc.search(q="file zip").total == 1
    assert svc.search(q="  file   ").total == svc.search(q="file").total


def test_terms_limit(svc):
    svc.search(q=" ".join(["a"] * 10))
    with pytest.raises(SearchValidationError):
        svc.search(q=" ".join(["a"] * 11))


def test_q_length_limit(svc):
    with pytest.raises(SearchValidationError):
        svc.search(q="a" * 101)


def test_invalid_material(svc):
    with pytest.raises(SearchValidationError):
        svc.search(material="WOOD")


@pytest.mark.parametrize("limit,offset", [(0, 0), (-1, 0), (10, -1)])
def test_invalid_limit_offset(svc, limit, offset):
    with pytest.raises(SearchValidationError):
        svc.search(limit=limit, offset=offset)


def test_limit_cap_pagination_and_order(svc):
    assert svc.search(limit=1000).limit == 100
    r = svc.search()
    assert names(r) == sorted(names(r))
    page = svc.search(limit=2, offset=2)
    assert page.total == r.total and names(page) == names(r)[2:4]


def test_filter_options(svc):
    f = svc.get_filter_options()
    assert f["materials"] == ["PVC", "PP", "BOARD"]
    assert f["sizes"] == ["A3", "A4", "A5", "FS"]
    assert f["customizations"] == ["COLOR", "LOGO PRINT"]
    assert "Files" in f["categories"]


# ---- API -----------------------------------------------------------------
def _load_flask_app():
    """dev/app.py is shadowed by the dev/app/ package, so load it by path."""
    os.environ.setdefault("SECRET_KEY", "test-secret")
    spec = importlib.util.spec_from_file_location("vnk2_flask_app", REPO / "dev" / "app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


@pytest.fixture()
def client(SessionFactory, monkeypatch):
    import dev.api.products as products

    monkeypatch.setattr(products, "SessionLocal", SessionFactory)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FLASK_ENV", raising=False)
    app = Flask(__name__)
    app.register_blueprint(products.products_bp)
    app.config.update(TESTING=True)
    return app.test_client()


def test_api_search_shape(client):
    r = client.get("/api/products/search?q=PVC%20File&material=PVC&size=A4")
    assert r.status_code == 200
    b = r.get_json()
    assert b["total"] == 2 and b["limit"] == 50 and b["offset"] == 0
    assert set(b["applied"]) == {"q", "material", "size", "customization", "category"}
    item = next(i for i in b["items"] if i["title"] == "Clear File Folder")
    for k in ("id", "sku", "title", "description", "category", "material", "sizes", "customizations",
              "price", "inventory", "image_url"):
        assert k in item
    assert item["sizes"] == ["A3", "A4"] and item["customizations"] == ["LOGO PRINT"]


def test_api_search_not_shadowed_by_product_id(client):
    r = client.get("/api/products/search")
    assert r.status_code == 200 and "items" in r.get_json()
    r = client.get("/api/products/filters")
    assert r.status_code == 200 and "materials" in r.get_json()


def test_api_zero_results_200(client):
    r = client.get("/api/products/search?q=zzzznonexistent")
    assert r.status_code == 200 and r.get_json()["total"] == 0 and r.get_json()["items"] == []


@pytest.mark.parametrize("qs", [
    "material=WOOD", "limit=abc", "offset=x", "limit=0", "offset=-1", "q=" + "a" * 101,
    "q=" + "+".join(["a"] * 11), "size=" + "x" * 65, "limit=12345678901",
])
def test_api_400s(client, qs):
    r = client.get("/api/products/search?" + qs)
    assert r.status_code == 400
    assert "error" in r.get_json()
    assert "Traceback" not in r.get_data(as_text=True)


def test_api_limit_capped(client):
    assert client.get("/api/products/search?limit=1000").get_json()["limit"] == 100


def test_api_filters(client):
    b = client.get("/api/products/filters").get_json()
    assert b["materials"] == ["PVC", "PP", "BOARD"] and "A4" in b["sizes"]


def test_api_cache_headers_by_env(client, monkeypatch):
    assert client.get("/api/products/search").headers["Cache-Control"] == "no-store"
    assert client.get("/api/products/filters").headers["Cache-Control"] == "no-store"
    monkeypatch.setenv("APP_ENV", "production")
    assert client.get("/api/products/search").headers["Cache-Control"] == "public, max-age=30"
    assert client.get("/api/products/filters").headers["Cache-Control"] == "public, max-age=60"


def test_api_existing_list_and_detail_unchanged(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    items = r.get_json()
    assert isinstance(items, list) and set(items[0]) == {"id", "sku", "title", "price", "inventory"}
    pid = items[0]["id"]
    d = client.get(f"/api/products/{pid}")
    assert d.status_code == 200 and set(d.get_json()) == {"id", "sku", "title", "description", "price", "inventory"}
    assert client.get("/api/products/does-not-exist").status_code == 404


def test_api_500_is_generic(client, monkeypatch):
    import dev.api.products as products

    def boom(*a, **k):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(products.ProductSearchService, "search", boom)
    r = client.get("/api/products/search")
    assert r.status_code == 500
    assert "secret internal detail" not in r.get_data(as_text=True)


def test_models_create_all_tables_and_indexes(SessionFactory):
    engine = SessionFactory.kw["bind"]
    insp = inspect(engine)
    assert {"product_sizes", "product_customizations"} <= set(insp.get_table_names())
    idx = {i["name"] for i in insp.get_indexes("products")}
    assert {"ix_products_material", "ix_products_category", "ix_products_is_active"} <= idx


def test_full_flask_app_has_search_ui_ids_and_routes():
    app = _load_flask_app()
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert {"/api/products/search", "/api/products/filters"} <= rules
    html = app.test_client().get("/").get_data(as_text=True)
    for i in ("product-search-input", "filter-material", "filter-size", "filter-customization",
              "clear-filters", "results-count", "product-grid", "no-results", "filters-panel", "search-error"):
        assert f'id="{i}"' in html, i
    script = html.split("VNK-2: product search + filters")[1].split("</script>")[0]
    assert "innerHTML" not in script
