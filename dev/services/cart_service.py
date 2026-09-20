from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dev.models import Cart, CartItem, Product


MAX_CART_LINE_QTY = 99


@dataclass(frozen=True)
class CartTotals:
    subtotal: Decimal
    item_count: int


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def get_or_create_cart(session: Session, customer_id: str) -> Cart:
    cart = session.execute(select(Cart).where(Cart.customer_id == customer_id)).scalar_one_or_none()
    if cart:
        return cart

    cart = Cart(customer_id=customer_id)
    session.add(cart)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        cart = session.execute(select(Cart).where(Cart.customer_id == customer_id)).scalar_one()
    return cart


def validate_quantity(quantity: int) -> None:
    if not isinstance(quantity, int):
        raise ValueError("quantity must be an integer")
    if quantity < 1:
        raise ValueError("quantity must be at least 1")
    if quantity > MAX_CART_LINE_QTY:
        raise ValueError(f"quantity must be <= {MAX_CART_LINE_QTY}")


def get_active_product(session: Session, product_id: str) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise ValueError("product not found")
    if not product.is_active:
        raise ValueError("product is inactive")
    return product


def add_item(session: Session, customer_id: str, product_id: str, quantity: int) -> Cart:
    validate_quantity(quantity)
    product = get_active_product(session, product_id)
    cart = get_or_create_cart(session, customer_id)

    item = session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    ).scalar_one_or_none()

    if item:
        new_qty = int(item.quantity) + int(quantity)
        validate_quantity(new_qty)
        item.quantity = new_qty
        item.unit_price = product.unit_price
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, unit_price=product.unit_price)
        session.add(item)

    session.flush()
    return cart


def set_item_quantity(session: Session, customer_id: str, product_id: str, quantity: int) -> Cart:
    validate_quantity(quantity)
    product = get_active_product(session, product_id)
    cart = get_or_create_cart(session, customer_id)

    item = session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    ).scalar_one_or_none()

    if not item:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, unit_price=product.unit_price)
        session.add(item)
    else:
        item.quantity = quantity
        item.unit_price = product.unit_price

    session.flush()
    return cart


def remove_item(session: Session, customer_id: str, product_id: str) -> Cart:
    cart = get_or_create_cart(session, customer_id)
    item = session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    ).scalar_one_or_none()

    if item:
        session.delete(item)
        session.flush()
    return cart


def clear_cart(session: Session, customer_id: str) -> Cart:
    cart = get_or_create_cart(session, customer_id)
    for item in list(cart.items):
        session.delete(item)
    session.flush()
    return cart


def totals_for_cart(cart: Cart) -> CartTotals:
    subtotal = Decimal("0")
    item_count = 0
    for item in cart.items:
        qty = int(item.quantity)
        item_count += qty
        subtotal += _to_decimal(item.unit_price) * Decimal(str(qty))
    return CartTotals(subtotal=subtotal, item_count=item_count)


def serialize_cart(cart: Cart) -> dict:
    totals = totals_for_cart(cart)

    items = []
    inactive_product_ids = []

    for item in cart.items:
        # product relationship might not be loaded; safe check.
        product = getattr(item, "product", None)
        is_active = None
        if product is not None:
            is_active = bool(product.is_active)

        if is_active is False:
            inactive_product_ids.append(item.product_id)

        line_total = _to_decimal(item.unit_price) * Decimal(str(int(item.quantity)))
        items.append(
            {
                "product_id": item.product_id,
                "quantity": int(item.quantity),
                "unit_price": float(_to_decimal(item.unit_price)),
                "line_total": float(line_total),
                "is_active": is_active,
            }
        )

    return {
        "customer_id": cart.customer_id,
        "items": items,
        "totals": {"subtotal": float(totals.subtotal), "item_count": totals.item_count},
        "inactive_product_ids": inactive_product_ids,
    }
