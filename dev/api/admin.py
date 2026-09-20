from flask import Blueprint, jsonify, request
from dev.auth import verify_password
from dev.db import SessionLocal
from dev.models import AdminUser, Order

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    with SessionLocal() as session:
        admin = session.query(AdminUser).filter_by(username=username).first()
        if not admin or not verify_password(password, admin.password_hash):
            return jsonify({'error': 'invalid credentials'}), 401
        return jsonify({'status': 'ok', 'admin_id': admin.id})

@admin_bp.route('/api/admin/orders')
def list_orders():
    with SessionLocal() as session:
        orders = session.query(Order).limit(50).all()
        # Return the canonical order status field (order_status) to match the
        # SQLAlchemy model. Previously used `o.status` which does not exist and
        # would raise an AttributeError at runtime.
        return jsonify([{'id': o.id, 'order_status': o.order_status} for o in orders])
