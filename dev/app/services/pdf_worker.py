"""Background PDF worker for invoice generation.

This is the minimal invoice rendering implementation used by the storefront
checkout and admin invoice flows. It writes PDF artifacts to the local storage
folder unless the environment is configured for S3/MinIO.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from dev.app.db import SessionLocal
from dev.app.models import Invoice, Order

STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")


def _ensure_storage_path() -> Path:
    p = Path(STORAGE_PATH) / "invoices"
    p.mkdir(parents=True, exist_ok=True)
    return p


def generate_invoice_pdf(invoice_id: str, db: Optional[Session] = None) -> Optional[str]:
    """Render a deterministic invoice PDF and persist its path to the database."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        inv = db.query(Invoice).filter(Invoice.id == invoice_id).one_or_none()
        if inv is None:
            raise ValueError(f"Invoice not found: {invoice_id}")

        order = db.query(Order).filter(Order.id == inv.order_id).one_or_none()
        if order is None:
            raise ValueError(f"Order not found for invoice: {invoice_id}")

        storage_dir = _ensure_storage_path()
        filename = f"invoice_{invoice_id}.pdf"
        full_path = storage_dir / filename

        c = canvas.Canvas(str(full_path), pagesize=A4)
        c.setTitle(f"Vinayaka File Works Invoice {invoice_id}")
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, 800, "Vinayaka File Works")
        c.setFont("Helvetica", 11)
        c.drawString(40, 782, f"Invoice No: {inv.id}")
        c.drawString(40, 768, f"Order Ref: {order.id}")
        c.drawString(40, 754, f"Customer: {order.customer.full_name if order.customer else 'Walk-in Customer'}")
        c.drawString(40, 740, f"Date: {datetime.utcnow().strftime('%Y-%m-%d')} ")

        y = 700
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Item")
        c.drawString(320, y, "Qty")
        c.drawString(420, y, "Unit")
        c.drawString(520, y, "Total")
        c.setFont("Helvetica", 11)
        y -= 18

        for item in order.items:
            product_name = item.product.name if item.product else "Product"
            c.drawString(40, y, product_name[:36])
            c.drawString(330, y, str(item.quantity))
            c.drawString(420, y, f"₹{float(item.unit_price):.2f}")
            c.drawString(520, y, f"₹{float(item.line_total):.2f}")
            y -= 18

        c.drawString(40, max(120, y - 20), "Subtotal")
        c.drawString(520, max(120, y - 20), f"₹{float(order.subtotal):.2f}")
        c.drawString(40, max(100, y - 38), "Total")
        c.drawString(520, max(100, y - 38), f"₹{float(order.total_amount):.2f}")
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(40, 52, "Thank you for shopping with Vinayaka File Works")
        c.showPage()
        c.save()

        inv.pdf_path = str(full_path)
        inv.status = "READY"
        inv.generated_at = datetime.utcnow()
        db.add(inv)
        db.commit()
        return str(full_path)
    except Exception:
        try:
            inv = db.query(Invoice).filter(Invoice.id == invoice_id).one_or_none()
            if inv:
                inv.status = "FAILED"
                db.add(inv)
                db.commit()
        except Exception:
            pass
        raise
    finally:
        if own_session:
            db.close()
