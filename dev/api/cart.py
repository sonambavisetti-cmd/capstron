from __future__ import annotations

from flask import Blueprint, jsonify, request

from dev.db import Base, SessionLocal, engine
from dev.services.cart_service import (
    add_item,
    clear_cart,
    get_or_create_cart,
    remove_item,
    serialize_cart,
    set_item_quantity,
)

cart_bp = Blueprint("cart", __name__)

# Ensure tables exist in environments that do not run migrations (dev/ demos).
Base.metadata.create_all(bind=engine)


def _bad_request(message: str):
    return jsonify({"error": message}), 400


def _read_json() -> dict:
    data = request.get_json(silent=True) or {}
    return data if isinstance(data, dict) else {}


@cart_bp.route("/api/cart/<customer_id>", methods=["GET"])
def get_cart(customer_id: str):
    if not str(customer_id or "").strip():
        return _bad_request("customer_id is required")

    with SessionLocal() as session:
        cart = get_or_create_cart(session, customer_id)
        # Load product relationship for is_active flag.
        for item in cart.items:
            _ = item.product
        session.commit()
        return jsonify(serialize_cart(cart))


# Backward-compatible endpoint
@cart_bp.route("/api/cart/<customer_id>/add", methods=["POST"])
def add_to_cart(customer_id: str):
    if not str(customer_id or "").strip():
        return _bad_request("customer_id is required")

    data = _read_json()

    # Backward compatible input: {"item": {"product_id": "...", "quantity": 1}}
    item = data.get("item") if isinstance(data.get("item"), dict) else data
    product_id = (item or {}).get("product_id")
    quantity = (item or {}).get("quantity", 1)

    try:
        quantity = int(quantity)
    except Exception:
        return _bad_request("quantity must be an integer")

    if not product_id:
        return _bad_request("product_id is required")

    try:
        with SessionLocal() as session:
            cart = add_item(session, customer_id, product_id, quantity)
            for ci in cart.items:
                _ = ci.product
            session.commit()
            return jsonify({"status": "ok", "cart": serialize_cart(cart)})
    except ValueError as exc:
        return _bad_request(str(exc))


@cart_bp.route("/api/cart/<customer_id>/items/<product_id>", methods=["PUT"])
def put_cart_item(customer_id: str, product_id: str):
    data = _read_json()

    if not str(customer_id or "").strip():
        return _bad_request("customer_id is required")
    if not str(product_id or "").strip():
        return _bad_request("product_id is required")

    if "quantity" not in data:
        return _bad_request("quantity is required")

    try:
        quantity = int(data.get("quantity"))
    except Exception:
        return _bad_request("quantity must be an integer")

    try:
        with SessionLocal() as session:
            cart = set_item_quantity(session, customer_id, product_id, quantity)
            for ci in cart.items:
                _ = ci.product
            session.commit()
            return jsonify({"status": "ok", "cart": serialize_cart(cart)})
    except ValueError as exc:
        return _bad_request(str(exc))


@cart_bp.route("/api/cart/<customer_id>/items/<product_id>", methods=["DELETE"])
def delete_cart_item(customer_id: str, product_id: str):
    if not str(customer_id or "").strip():
        return _bad_request("customer_id is required")
    if not str(product_id or "").strip():
        return _bad_request("product_id is required")

    with SessionLocal() as session:
        cart = remove_item(session, customer_id, product_id)
        for ci in cart.items:
            _ = ci.product
        session.commit()
        return jsonify({"status": "ok", "cart": serialize_cart(cart)})


@cart_bp.route("/api/cart/<customer_id>", methods=["DELETE"])
def delete_cart(customer_id: str):
    if not str(customer_id or "").strip():
        return _bad_request("customer_id is required")

    with SessionLocal() as session:
        cart = clear_cart(session, customer_id)
        session.commit()
        return jsonify({"status": "ok", "cart": serialize_cart(cart)})
