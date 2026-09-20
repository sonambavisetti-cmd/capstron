from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from dev.db import SessionLocal
from dev.models import Invoice, Order
from dev.storage.local import LocalStorage

STORAGE = LocalStorage(base_path=os.path.join(os.getcwd(), 'storage'))


def generate_invoice(order_id: str) -> Optional[str]:
    """Generate a deterministic invoice PDF for the given order."""
    with SessionLocal() as session:
        order = session.get(Order, order_id)
        if not order:
            return None

        inv = session.query(Invoice).filter_by(order_id=order_id).first()
        if not inv:
            inv = Invoice(order_id=order_id, status='PENDING')
            session.add(inv)
            session.flush()

        output_dir = Path(os.getenv('STORAGE_PATH', os.path.join(os.getcwd(), 'storage'))) / 'invoices'
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"invoice_{inv.id}.pdf"
        path = output_dir / filename

        c = canvas.Canvas(str(path), pagesize=A4)
        c.setTitle(f"Vinayaka File Works Invoice {inv.id}")
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, 800, "Vinayaka File Works")
        c.setFont("Helvetica", 11)
        c.drawString(40, 782, "Invoice Date: %s" % datetime.utcnow().strftime('%Y-%m-%d'))
        c.drawString(40, 768, f"Invoice No: {inv.id}")
        c.drawString(40, 754, f"Order Ref: {order.id}")
        c.drawString(40, 740, f"Customer: {order.customer.full_name if order.customer else 'Walk-in Customer'}")
        c.drawString(40, 726, f"Email: {order.customer.email if order.customer and order.customer.email else 'n/a'}")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, 680, "Item")
        c.drawString(350, 680, "Qty")
        c.drawString(450, 680, "Price")
        c.drawString(520, 680, "Total")
        c.setFont("Helvetica", 11)

        y = 660
        for item in order.items:
            product_name = item.product.name if item.product else 'Product'
            c.drawString(40, y, product_name[:40])
            c.drawString(360, y, str(item.quantity))
            c.drawString(450, y, f"₹{float(item.unit_price):.2f}")
            c.drawString(520, y, f"₹{float(item.line_total):.2f}")
            y -= 20

        c.drawString(40, max(120, y - 20), "Subtotal")
        c.drawString(520, max(120, y - 20), f"₹{float(order.subtotal):.2f}")
        c.drawString(40, max(100, y - 40), "Total")
        c.drawString(520, max(100, y - 40), f"₹{float(order.total_amount):.2f}")
        c.drawString(40, 60, "Thank you for ordering with Vinayaka File Works")
        c.save()

        inv.pdf_path = str(path)
        inv.status = 'READY'
        session.commit()
        return str(path)
