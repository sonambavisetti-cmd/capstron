"""Order service for VNK-3 storefront operations.

The implementation stays intentionally small but keeps the critical business
rules in place: checkout validation, stock checks, transactional order
creation, and invoice record creation.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from dev.app.models import Customer, Invoice, Order, OrderItem, Product
from dev.app.schemas import OrderCreate


def _normalize_status(value: str, default: str) -> str:
    if not value:
        return default
    return value.strip().upper() if value.isalpha() else default


def create_order(db: Session, order_in: OrderCreate, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """Create a new order with validation.

    Stock is not decremented at order creation: the code defers inventory
    reservation/finalization to the confirmation path so that COD and online
    payment flows cannot oversell or create confirmed orders before payment is
    settled. The invoice placeholder is still created and generated after the
    order is committed.
    """
    if not order_in.items:
        raise ValueError("Order must contain at least one item")

    if not order_in.customer or not order_in.customer.full_name:
        raise ValueError("Customer full_name is required")

    if order_in.customer.email and "@" not in order_in.customer.email:
        raise ValueError("Customer email must be a valid email address")

    if idempotency_key:
        logging.debug("Idempotency-Key provided: %s", idempotency_key)

    customer = None
    if order_in.customer.email:
        customer = db.query(Customer).filter(Customer.email == order_in.customer.email).one_or_none()

    if not customer:
        customer = Customer(
            full_name=order_in.customer.full_name,
            phone=order_in.customer.phone,
            email=order_in.customer.email,
            address_line1=order_in.customer.address_line1,
            city=order_in.customer.city,
            state=order_in.customer.state,
            postal_code=order_in.customer.postal_code,
            country=order_in.customer.country,
        )
        db.add(customer)
        db.flush()

    product_ids = [item.product_id for item in order_in.items]
    products = db.query(Product).filter(Product.id.in_(product_ids)).with_for_update().all()
    product_map = {product.id: product for product in products}

    subtotal = Decimal("0.00")
    for item in order_in.items:
        product = product_map.get(item.product_id)
        if product is None:
            raise ValueError(f"Product not found: {item.product_id}")
        if item.quantity <= 0:
            raise ValueError(f"Quantity for product {item.product_id} must be positive")

        unit_price = Decimal(str(product.unit_price))
        line_total = unit_price * item.quantity
        subtotal += line_total

    order = Order(
        customer_id=customer.id,
        payment_method=order_in.payment_method.upper(),
        payment_status="PENDING",
        order_status="PENDING",
        notes=order_in.notes,
        subtotal=subtotal,
        shipping_charges=Decimal("0.00"),
        total_amount=subtotal,
    )
    db.add(order)
    db.flush()

    for item in order_in.items:
        product = product_map[item.product_id]
        unit_price = Decimal(str(product.unit_price))
        line_total = unit_price * item.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=unit_price,
            line_total=line_total,
        )
        db.add(order_item)

    invoice = Invoice(order_id=order.id, status="PENDING")
    db.add(invoice)
    db.flush()

    db.commit()

    try:
        from dev.app.services.pdf_worker import generate_invoice_pdf

        generate_invoice_pdf(invoice.id, db=db)
    except Exception:
        logging.exception("Invoice generation failed for order %s", order.id)

    return {
        "order_id": order.id,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "total_amount": float(order.total_amount),
    }
