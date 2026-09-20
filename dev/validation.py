import re
from typing import Any, Dict


def validate_order_payload(payload: Dict[str, Any]) -> None:
    if 'items' not in payload or not isinstance(payload['items'], list) or len(payload['items']) == 0:
        raise ValueError('order must contain items')
    if 'customer' not in payload or 'email' not in payload['customer']:
        raise ValueError('customer.email required')

    for item in payload['items']:
        if not item.get('product_id'):
            raise ValueError('each item requires product_id')
        qty = item.get('quantity', 1)
        if not isinstance(qty, int) or qty <= 0:
            raise ValueError('quantity must be a positive integer')


def validate_quote_enquiry_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError('quote request payload is required')

    normalized = {}
    aliases = {
        'name': ['name', 'full_name', 'customer_name'],
        'company': ['company', 'company_name', 'organization'],
        'mobile_number': ['mobile_number', 'phone', 'mobile', 'contact_number'],
        'email': ['email', 'email_address'],
        'product_category': ['product_category', 'product', 'category', 'product_name'],
        'required_quantity': ['required_quantity', 'quantity', 'qty'],
        'customization_requirements': ['customization_requirements', 'requirements', 'customization'],
        'preferred_contact_method': ['preferred_contact_method', 'contact_method', 'preferred_contact'],
        'additional_message': ['additional_message', 'message', 'notes'],
    }

    for canonical, options in aliases.items():
        for option in options:
            if option in payload and payload.get(option) is not None:
                normalized[canonical] = payload.get(option)
                break

    if not str(normalized.get('name', '')).strip():
        raise ValueError('name is required')
    if not str(normalized.get('mobile_number', '')).strip():
        raise ValueError('mobile_number is required')
    if not str(normalized.get('product_category', '')).strip():
        raise ValueError('product_category is required')

    mobile = str(normalized.get('mobile_number', '')).strip()
    digits = re.sub(r'\D', '', mobile)
    if len(digits) < 10:
        raise ValueError('mobile_number must include at least 10 digits')

    email = str(normalized.get('email', '')).strip()
    if email and '@' not in email:
        raise ValueError('email must be a valid email address')

    normalized['name'] = str(normalized['name']).strip()
    normalized['company'] = str(normalized.get('company', '') or '').strip()
    normalized['mobile_number'] = mobile
    normalized['email'] = email
    normalized['product_category'] = str(normalized['product_category']).strip()
    normalized['required_quantity'] = str(normalized.get('required_quantity', '') or '').strip()
    normalized['customization_requirements'] = str(normalized.get('customization_requirements', '') or '').strip()
    normalized['preferred_contact_method'] = str(normalized.get('preferred_contact_method', '') or '').strip() or 'Call'
    normalized['additional_message'] = str(normalized.get('additional_message', '') or '').strip()

    return normalized
