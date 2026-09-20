"""Application models adapter.

The repository provides SQLAlchemy models under `dev.models`. To keep the
new `dev.app` package self-contained for import paths used in the Phase 5
implementation, this module re-exports the model classes from `dev.models`.

This avoids duplicating model definitions while satisfying the deliverable
that `dev/app/models.py` exists.
"""
from dev import models as core_models  # re-use the canonical model definitions

# Re-export commonly used model classes for convenience
Product = core_models.Product
Customer = core_models.Customer
Order = core_models.Order
OrderItem = core_models.OrderItem
Invoice = core_models.Invoice
QuoteEnquiry = getattr(core_models, "QuoteEnquiry")
QuoteRequest = QuoteEnquiry
QuoteInquiry = QuoteEnquiry
AdminUser = core_models.AdminUser
SiteSettings = getattr(core_models, "SiteSettings", None)  # may not exist yet

__all__ = [
    "Product",
    "Customer",
    "Order",
    "OrderItem",
    "Invoice",
    "QuoteEnquiry",
    "QuoteRequest",
    "QuoteInquiry",
    "AdminUser",
    "SiteSettings",
]
