import os
from decimal import Decimal

from dev.db import init_db, SessionLocal
from dev.models import Product, Customer, Order, OrderItem, Invoice
from dev.app.services.pdf_worker import generate_invoice_pdf, STORAGE_PATH


def setup_module(module):
    init_db()


def test_generate_invoice_creates_file():
    db = SessionLocal()
    # create product
    p = Product(sku="PDF-001", name="PDF Prod", unit_price=Decimal("50.00"), quantity_available=5)
    db.add(p)
    db.commit()

    # create customer and order
    cust = Customer(full_name="PDF User", email="pdf@example.com")
    db.add(cust)
    db.flush()

    order = Order(customer_id=cust.id, payment_method="COD", subtotal=Decimal("50.00"), total_amount=Decimal("50.00"))
    db.add(order)
    db.flush()

    oi = OrderItem(order_id=order.id, product_id=p.id, quantity=1, unit_price=Decimal("50.00"), line_total=Decimal("50.00"))
    db.add(oi)

    inv = Invoice(order_id=order.id, status="PENDING")
    db.add(inv)
    db.commit()

    pdf_path = generate_invoice_pdf(inv.id, db=db)
    assert pdf_path is not None
    assert os.path.exists(pdf_path)

    # cleanup file
    try:
        os.remove(pdf_path)
    except Exception:
        pass

    db.close()
