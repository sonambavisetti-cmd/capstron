"""Compatibility wrapper for validation helpers used by the storefront."""

from dev.validation import validate_order_payload, validate_quote_enquiry_payload

__all__ = ["validate_order_payload", "validate_quote_enquiry_payload"]
