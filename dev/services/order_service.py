from decimal import Decimal
from typing import Any, Dict

from dev.db import SessionLocal
from dev.models import Customer, Invoice, Order, OrderItem, Product
from dev.payments.mock import MockPayment
from dev.validation import validate_order_payload

payment_provider = MockPayment()


def create_order(payload: Dict[str, Any]) -> Order:
    validate_order_payload(payload)
    items = payload['items']
    customer_data = payload.get('customer', {})

    with SessionLocal() as session:
        customer_email = customer_data.get('email')
        cust = session.query(Customer).filter_by(email=customer_email).first()
        if not cust:
            cust = Customer(
                email=customer_email,
                full_name=customer_data.get('full_name') or customer_data.get('name') or 'Customer',
            )
            session.add(cust)
            session.flush()

        order = Order(customer_id=cust.id, order_status='PENDING', total_amount=0, subtotal=0, shipping_charges=0)
        session.add(order)
        session.flush()

        total_amount = Decimal('0')
        for item in items:
            product_id = item.get('product_id')
            qty = int(item.get('quantity', 1))
            if qty <= 0:
                raise ValueError('quantity must be positive')

            product = session.get(Product, product_id)
            if not product:
                raise ValueError(f'product {product_id} not found')
            if product.quantity_available < qty:
                raise ValueError(f'not enough inventory for product {product_id}')

            product.quantity_available -= qty
            unit_price = Decimal(str(product.unit_price))
            line_total = unit_price * qty
            total_amount += line_total

            session.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                line_total=line_total,
            ))

        order.subtotal = total_amount
        order.total_amount = total_amount
        order.payment_method = payload.get('payment', {}).get('method', 'COD')
        order.payment_status = 'PENDING'
        session.flush()

        pay = payment_provider.charge(
            int(total_amount * 100),
            'USD',
            payload.get('payment', {}),
            payload.get('idempotency_key', ''),
        )
        if not pay.success:
            raise ValueError('payment failed')

        order.payment_status = 'SUCCESS'
        order.order_status = 'PROCESSING'
        session.add(Invoice(order_id=order.id, status='PENDING', pdf_path=None))
        session.commit()

        from dev.services.invoice import generate_invoice
        generate_invoice(order.id)
        return order
