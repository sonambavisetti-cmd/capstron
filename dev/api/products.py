from flask import Blueprint, jsonify, request
from dev.db import SessionLocal
from dev.models import Product

products_bp = Blueprint('products', __name__)

@products_bp.route('/api/products')
def list_products():
    """Supports ?page=1&per_page=10."""
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = max(1, min(100, int(request.args.get('per_page', 10))))
    except ValueError:
        return jsonify({'error': 'page and per_page must be integers'}), 400

    with SessionLocal() as session:
        q = session.query(Product).offset((page - 1) * per_page).limit(per_page)
        items = [
            {
                'id': p.id,
                'sku': p.sku,
                'title': p.name,
                'price': float(p.unit_price or 0),
                'inventory': p.quantity_available,
            } for p in q
        ]

    resp = jsonify(items)
    resp.headers['Cache-Control'] = 'public, max-age=30'
    return resp

@products_bp.route('/api/products/<product_id>')
def get_product(product_id: str):
    with SessionLocal() as session:
        p = session.get(Product, product_id)
        if not p:
            return jsonify({'error': 'not found'}), 404
        return jsonify({
            'id': p.id,
            'sku': p.sku,
            'title': p.name,
            'description': p.description,
            'price': float(p.unit_price or 0),
            'inventory': p.quantity_available,
        })
