"""Pydantic request and response schemas for the FastAPI surface.

Keep schemas minimal for the Phase 5 skeleton. Add fields as needed when
implementing full business logic. Use type hints and validation where useful.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: str
    sku: str
    name: str
    description: Optional[str]
    unit_price: float
    quantity_available: int
    image_url: Optional[str]


class CustomerIn(BaseModel):
    full_name: str
    phone: Optional[str] = None
    # Avoid pydantic[email] extra dependency in tests by using plain str here.
    email: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class OrderItemIn(BaseModel):
    product_id: str = Field(..., alias="product_id")
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer: CustomerIn
    items: List[OrderItemIn]
    # Use `pattern` (pydantic v2) instead of the removed `regex` kwarg
    payment_method: str = Field("COD", pattern="^(COD|ONLINE)$")
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    order_id: str
    order_status: str
    payment_status: str
    total_amount: float


class PaymentSessionCreate(BaseModel):
    order_id: str
    amount_cents: int


class PaymentSessionOut(BaseModel):
    session_id: str
    url: Optional[str]
    status: str


class InvoiceResponse(BaseModel):
    invoice_id: str
    status: str
    download_url: Optional[str]


class AdminLogin(BaseModel):
    username: str
    password: str


class SiteSettingsOut(BaseModel):
    company_name: str
    tagline: str
    phone: str
    email: str
    address: str
    city: str
    state: str
    pincode: str


class CartItemIn(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class CartRequest(BaseModel):
    items: List[CartItemIn]


class CartLineOut(BaseModel):
    product_id: str
    sku: str
    name: str
    quantity: int
    unit_price: float
    line_total: float


class CartSummaryOut(BaseModel):
    items: List[CartLineOut]
    subtotal: float
    shipping: float = 0.0
    total: float
    currency: str = "INR"


class AdminStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|confirmed|processed|cancelled|PENDING|CONFIRMED|PROCESSED|CANCELLED)$")


class AdminOrderOut(BaseModel):
    order_id: str
    customer_name: str
    total_amount: float
    order_status: str
    payment_status: str
