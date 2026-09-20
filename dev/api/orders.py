from flask import Blueprint, jsonify, request
from dev.services.order_service import create_order

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/api/orders', methods=['POST'])
def post_order():
    payload = request.json or {}
    try:
        order = create_order(payload)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'status': 'created', 'order_id': order.id}), 201

@orders_bp.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id: str):
    from dev.db import SessionLocal
    from dev.models import Order
    with SessionLocal() as session:
        o = session.get(Order, order_id)
        if not o:
            return jsonify({'error': 'not found'}), 404
        return jsonify({'id': o.id, 'status': o.order_status, 'total_amount': float(o.total_amount)})
