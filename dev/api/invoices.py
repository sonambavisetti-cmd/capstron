from flask import Blueprint, jsonify, send_file, abort
from dev.db import SessionLocal
from dev.models import Invoice
import os

invoices_bp = Blueprint('invoices', __name__)

@invoices_bp.route('/api/orders/<order_id>/invoice')
def get_invoice_for_order(order_id: str):
    with SessionLocal() as session:
        inv = session.query(Invoice).filter_by(order_id=order_id).first()
        if not inv:
            return jsonify({'error': 'invoice not found'}), 404
        # Provide a simple download URL for tests
        download_url = f"/api/invoices/{inv.id}/download"
        return jsonify({'id': inv.id, 'status': inv.status, 'download_url': download_url, 'pdf_path': inv.pdf_path})


@invoices_bp.route('/api/invoices/<invoice_id>/download')
def download_invoice(invoice_id: str):
    with SessionLocal() as session:
        inv = session.get(Invoice, invoice_id)
        if not inv or not inv.pdf_path:
            return jsonify({'error': 'not found'}), 404
        # If file exists on disk, send it as attachment; otherwise 404
        if not os.path.exists(inv.pdf_path):
            return jsonify({'error': 'file not found'}), 404
        # Use Flask's send_file to return the file content.
        # For local dev the invoice may be a text file pretending to be a PDF.
        try:
            return send_file(inv.pdf_path, as_attachment=True)
        except Exception:
            # Fallback: read and return raw bytes
            with open(inv.pdf_path, 'rb') as f:
                data = f.read()
            return (data, 200, {'Content-Type': 'application/octet-stream'})
