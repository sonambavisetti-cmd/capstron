import logging
import os

from flask import Blueprint, jsonify, request
from dev.db import SessionLocal
from dev.models import Product
from dev.services.product_search import ProductSearchService, SearchValidationError

products_bp = Blueprint('products', __name__)
logger = logging.getLogger(__name__)

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

def _is_production() -> bool:
    env = (os.getenv('APP_ENV') or os.getenv('FLASK_ENV') or 'development').lower()
    return env == 'production'


def _set_cache(resp, max_age: int):
    # F-06: cache only in production; no-store elsewhere to keep tests deterministic.
    resp.headers['Cache-Control'] = f'public, max-age={max_age}' if _is_production() else 'no-store'
    return resp


def _parse_int(name: str, default: int):
    raw = request.args.get(name)
    if raw is None or raw.strip() == '':
        return default
    if len(raw) > 10:
        raise SearchValidationError(f'{name} must be an integer')
    try:
        return int(raw.strip())
    except ValueError:
        raise SearchValidationError(f'{name} must be an integer')


def _serialize_search_item(p: Product) -> dict:
    return {
        'id': p.id,
        'sku': p.sku,
        'title': p.name,
        'description': p.description,
        'category': p.category,
        'material': (p.material or None),
        'sizes': sorted(s.size for s in p.sizes),
        'customizations': sorted(c.option for c in p.customizations),
        'price': float(p.unit_price or 0),
        'inventory': p.quantity_available,
        'image_url': p.image_url,
    }


@products_bp.route('/api/products/search')
def search_products():
    """GET /api/products/search?q=&material=&size=&customization=&category=&limit=&offset="""
    try:
        limit = _parse_int('limit', 50)
        offset = _parse_int('offset', 0)
        with SessionLocal() as session:
            result = ProductSearchService(session).search(
                q=request.args.get('q'),
                material=request.args.get('material'),
                size=request.args.get('size'),
                customization=request.args.get('customization'),
                category=request.args.get('category'),
                limit=limit,
                offset=offset,
            )
            body = {
                'items': [_serialize_search_item(p) for p in result.items],
                'total': result.total,
                'limit': result.limit,
                'offset': result.offset,
                'applied': result.applied,
            }
    except SearchValidationError as exc:
        resp = jsonify({'error': str(exc)})
        resp.status_code = 400
        resp.headers['Cache-Control'] = 'no-store'
        return resp
    except Exception:
        logger.exception('product search failed')
        resp = jsonify({'error': 'Unable to search products'})
        resp.status_code = 500
        resp.headers['Cache-Control'] = 'no-store'
        return resp
    return _set_cache(jsonify(body), 30)


@products_bp.route('/api/products/filters')
def product_filters():
    try:
        with SessionLocal() as session:
            options = ProductSearchService(session).get_filter_options()
    except Exception:
        logger.exception('product filters failed')
        resp = jsonify({'error': 'Unable to load filters'})
        resp.status_code = 500
        resp.headers['Cache-Control'] = 'no-store'
        return resp
    return _set_cache(jsonify(options), 60)


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
