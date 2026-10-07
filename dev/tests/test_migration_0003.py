"""Migration 0003 tests on TEMP COPIES only; the working-tree dev.db is never opened.

The source is `git show HEAD:dev.db` (stamped 0001 but already holding 0002 tables); the copy is
re-stamped 0002 before upgrading. A temp alembic ini is used because the repo alembic.ini is not
usable for programmatic runs here.
"""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO = Path(__file__).resolve().parents[2]

INI = """[alembic]
script_location = {script}
sqlalchemy.url = {url}

[loggers]
keys = root

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
"""


def _cfg(tmp_path: Path, db: Path) -> Config:
    ini = tmp_path / "alembic_tmp.ini"
    ini.write_text(INI.format(script=(REPO / "alembic").as_posix(), url=f"sqlite:///{db.as_posix()}"))
    return Config(str(ini))


def _cols(db: Path, table: str):
    with sqlite3.connect(db) as c:
        return {r[1] for r in c.execute(f'PRAGMA table_info("{table}")')}


def _tables(db: Path):
    with sqlite3.connect(db) as c:
        return {r[0] for r in c.execute("select name from sqlite_master where type='table'")}


def _indexes(db: Path):
    with sqlite3.connect(db) as c:
        return {r[0] for r in c.execute("select name from sqlite_master where type='index'")}


@pytest.fixture()
def db_copy(tmp_path):
    db = tmp_path / "dev_copy.db"
    try:
        data = subprocess.run(["git", "show", "HEAD:dev.db"], cwd=REPO, capture_output=True, check=True).stdout
    except Exception as exc:
        pytest.skip(f"HEAD:dev.db unavailable: {exc}")
    if not data.startswith(b"SQLite format 3"):
        pytest.skip("HEAD:dev.db is not a SQLite file")
    db.write_bytes(data)
    if "products" not in _tables(db):
        pytest.skip("HEAD:dev.db has no products table")
    assert "material" not in _cols(db, "products"), "copy already has 0003 columns"
    cfg = _cfg(tmp_path, db)
    if "alembic_version" in _tables(db):
        with sqlite3.connect(db) as c:
            c.execute("delete from alembic_version")
            c.commit()
    command.stamp(cfg, "0002_add_cart_tables")
    return db, cfg


def test_upgrade_downgrade_upgrade_on_dev_db_copy(db_copy):
    db, cfg = db_copy
    with sqlite3.connect(db) as c:
        before = c.execute("select count(*) from products").fetchone()[0]
        ids_before = {r[0] for r in c.execute("select id from products")}

    command.upgrade(cfg, "head")
    assert {"category", "material", "specifications"} <= _cols(db, "products")
    assert {"product_sizes", "product_customizations"} <= _tables(db)
    assert {"ix_products_material", "ix_products_category", "ix_products_is_active",
            "ix_product_sizes_size_product", "ix_product_customizations_option_product"} <= _indexes(db)
    with sqlite3.connect(db) as c:
        assert c.execute("select count(*) from products").fetchone()[0] == before
        assert {r[0] for r in c.execute("select id from products")} == ids_before
        assert c.execute("select version_num from alembic_version").fetchone()[0] == "0003_product_search_attrs"

    command.downgrade(cfg, "0002_add_cart_tables")
    assert not ({"category", "material", "specifications"} & _cols(db, "products"))
    assert not ({"product_sizes", "product_customizations"} & _tables(db))
    assert not ({"ix_products_material", "ix_products_category", "ix_products_is_active"} & _indexes(db))
    with sqlite3.connect(db) as c:
        assert c.execute("select count(*) from products").fetchone()[0] == before

    command.upgrade(cfg, "head")
    assert {"category", "material", "specifications"} <= _cols(db, "products")


def test_search_service_works_on_migrated_copy(db_copy):
    db, cfg = db_copy
    command.upgrade(cfg, "head")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from dev.models import Product, ProductSize
    from dev.services.product_search import ProductSearchService

    engine = create_engine(f"sqlite:///{db.as_posix()}", future=True)
    with sessionmaker(bind=engine, future=True)() as s:
        p = Product(sku="MIG-1", name="Migrated File", unit_price=1, quantity_available=1, is_active=True,
                    material="PVC", category="Files")
        p.sizes.append(ProductSize(size="A4"))
        s.add(p)
        s.commit()
        r = ProductSearchService(s).search(q="PVC File", size="A4")
        assert [i.sku for i in r.items] == ["MIG-1"]
    engine.dispose()
