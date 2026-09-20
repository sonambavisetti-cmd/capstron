from __future__ import annotations

from flask import Blueprint, jsonify, request

from dev.db import Base, SessionLocal, engine
from dev.models import QuoteEnquiry
from dev.validation import validate_quote_enquiry_payload

quote_bp = Blueprint("quote_requests", __name__)

# Ensure table exists in environments that do not run migrations (dev/ demos).
Base.metadata.create_all(bind=engine)


def _read_payload():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict() or {}
    if not isinstance(data, dict):
        data = {}
    return data


@quote_bp.route("/api/quote-requests", methods=["POST"])
@quote_bp.route("/api/quote-enquiries", methods=["POST"])
def create_quote_request():
    payload = _read_payload()
    try:
        clean = validate_quote_enquiry_payload(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    with SessionLocal() as session:
        enquiry = QuoteEnquiry(
            name=clean["name"],
            company=clean["company"] or None,
            mobile_number=clean["mobile_number"],
            email=clean["email"] or None,
            product_category=clean["product_category"],
            required_quantity=clean["required_quantity"] or None,
            customization_requirements=clean["customization_requirements"] or None,
            preferred_contact_method=clean["preferred_contact_method"],
            additional_message=clean["additional_message"] or None,
        )
        session.add(enquiry)
        session.commit()
        session.refresh(enquiry)

    return (
        jsonify(
            {
                "status": "created",
                "quote_id": enquiry.id,
                "message": "Your request has been submitted successfully.",
            }
        ),
        201,
    )


@quote_bp.route("/api/quote-requests", methods=["GET"])
@quote_bp.route("/api/quote-enquiries", methods=["GET"])
def list_quote_requests():
    with SessionLocal() as session:
        rows = session.query(QuoteEnquiry).order_by(QuoteEnquiry.created_at.desc()).all()
        return jsonify(
            {
                "items": [
                    {
                        "id": row.id,
                        "name": row.name,
                        "company": row.company,
                        "mobile_number": row.mobile_number,
                        "email": row.email,
                        "product_category": row.product_category,
                        "required_quantity": row.required_quantity,
                        "status": row.status,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }
                    for row in rows
                ]
            }
        )
