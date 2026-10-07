from __future__ import annotations
"""Seed SAMPLE products for VNK-2 product search and filter.

Usage (run explicitly from the repo root; never runs on app start):
    python -m dev.scripts.seed_products

The target database is selected by the DATABASE_URL env var (default sqlite:///dev.db).
The schema must already be migrated (`alembic upgrade head`); on a brand-new empty
database missing tables are created non-destructively via create_all().
The script is idempotent: products are upserted by SKU and their sizes and
customization options are synchronised to the lists below.

This is sample data only; there is no real catalog source yet (risk R-01).
"""
from decimal import Decimal
from typing import Dict, List, Tuple

from dev.db import Base, SessionLocal, engine
from dev.models import Product, ProductCustomization, ProductSize

# sku, name, category, material, specifications, price, qty, sizes, customizations, active
SAMPLES: List[Dict] = [
    # F-01 fixture: name/specifications do not contain "PVC"; material does.
    dict(sku="SMP-FILE-A4-CLR", name="Clear File Folder", category="Files",
         material="PVC", specifications="Transparent cover, 20 pockets, reinforced edge",
         price="149.00", qty=120, sizes=["A4", "A3"], custom=["LOGO PRINT", "COLOR"], active=True),
    dict(sku="SMP-FILE-A4-DOC", name="Document File Premium", category="Files",
         material="PVC", specifications="Zip closure, heavy duty, waterproof",
         price="199.00", qty=80, sizes=["A4", "FS"], custom=["LOGO PRINT"], active=True),
    dict(sku="SMP-FILE-FS-EXP", name="Expanding File Organizer", category="Files",
         material="PVC", specifications="13 pockets, elastic closure",
         price="249.00", qty=45, sizes=["FS"], custom=[], active=True),
    dict(sku="SMP-FILE-A4-PP", name="Poly Ring File", category="Files",
         material="PP", specifications="2 D-ring binder, lightweight",
         price="99.00", qty=200, sizes=["A4"], custom=["COLOR"], active=True),
    dict(sku="SMP-FOLD-A3-PP", name="Project Folder", category="Folders",
         material="PP", specifications="Flap folder, rigid finish",
         price="59.00", qty=300, sizes=["A3", "A5"], custom=["COLOR", "EMBOSSING"], active=True),
    dict(sku="SMP-BOX-A4-BRD", name="Archive Box File", category="Boxes",
         material="BOARD", specifications="Lever arch, 75 mm spine, laminated board",
         price="179.00", qty=60, sizes=["A4", "FS"], custom=["LOGO PRINT", "EMBOSSING"], active=True),
    dict(sku="SMP-REG-A5-BRD", name="Printed Register", category="Registers",
         material="BOARD", specifications="Hardbound, 200 pages, ruled",
         price="129.00", qty=90, sizes=["A5"], custom=[], active=True),
    dict(sku="SMP-PAD-A4-BRD", name="Writing Pad", category="Stationery",
         material="BOARD", specifications="Board back, 100 sheets",
         price="49.00", qty=500, sizes=["A4", "A5"], custom=[], active=True),
    dict(sku="SMP-FILE-A4-OLD", name="Discontinued PVC File", category="Files",
         material="PVC", specifications="No longer sold",
         price="89.00", qty=0, sizes=["A4"], custom=[], active=False),
]


def _norm(value: str) -> str:
    return value.strip().upper()


def seed() -> Tuple[int, int, int, int]:
    Base.metadata.create_all(bind=engine)  # non-destructive; adds only missing tables
    with SessionLocal() as session:
        for s in SAMPLES:
            product = session.query(Product).filter_by(sku=s["sku"]).first()
            if product is None:
                product = Product(sku=s["sku"])
                session.add(product)
            product.name = s["name"]
            product.description = s["specifications"]
            product.category = s["category"]
            product.material = _norm(s["material"])
            product.specifications = s["specifications"]
            product.unit_price = Decimal(s["price"])
            product.quantity_available = s["qty"]
            product.is_active = s["active"]
            session.flush()

            wanted_sizes = {_norm(x) for x in s["sizes"]}
            for row in list(product.sizes):
                if row.size not in wanted_sizes:
                    product.sizes.remove(row)
            have = {r.size for r in product.sizes}
            for size in sorted(wanted_sizes - have):
                product.sizes.append(ProductSize(size=size))

            wanted_opts = {_norm(x) for x in s["custom"]}
            for row in list(product.customizations):
                if row.option not in wanted_opts:
                    product.customizations.remove(row)
            have_o = {r.option for r in product.customizations}
            for opt in sorted(wanted_opts - have_o):
                product.customizations.append(ProductCustomization(option=opt))
        session.commit()

        return (
            session.query(Product).count(),
            session.query(Product).filter(Product.is_active.is_(True)).count(),
            session.query(ProductSize).count(),
            session.query(ProductCustomization).count(),
        )


if __name__ == "__main__":
    products, active, sizes, customs = seed()
    print(f"products={products} active={active} sizes={sizes} customizations={customs}")
