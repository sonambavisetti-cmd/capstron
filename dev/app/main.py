"""FastAPI entry point for the VNK-3 storefront MVP.

This module exposes the minimal storefront and admin API required by the
architecture and implementation plan while keeping the implementation focused on
core workflows: product catalog, cart/checkout, order persistence, invoice
metadata, and admin order processing.
"""
from __future__ import annotations

import logging
import os
import uuid
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from dev.app import db as app_db
from dev.app import schemas
from dev.app.auth import hash_password, verify_password
from dev.app.models import AdminUser, Invoice, Order, OrderItem, Product
from dev.app.services import order_service, payment_adapter
from dev.app.services.pdf_worker import generate_invoice_pdf

app = FastAPI(title="Vinayaka File Works", version="0.1.0")
logger = logging.getLogger(__name__)

SESSION_STORE: Dict[str, str] = {}
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
APP_ENV = os.getenv("APP_ENV", "development").lower()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_SITE_SETTINGS = {
    "company_name": "Vinayaka File Works",
    "tagline": "Print, packaging and stationery for everyday business",
    "phone": "+91 98765 43210",
    "email": "hello@vinayakafileworks.com",
    "address": "7A Market Road",
    "city": "Bengaluru",
    "state": "Karnataka",
    "pincode": "560001",
}


def get_db() -> Session:
    return next(app_db.get_db())


def ensure_seed_data(db: Session) -> None:
    default_products = [
        {
            "sku": "VFW-1001",
            "name": "A4 Copier Paper",
            "description": "Premium A4 paper pack",
            "unit_price": Decimal("349.00"),
            "quantity_available": 25,
            "image_url": "https://example.com/paper.jpg",
            "is_active": True,
        },
        {
            "sku": "VFW-1002",
            "name": "Business Card Stock",
            "description": "Matte business card sheet",
            "unit_price": Decimal("199.00"),
            "quantity_available": 40,
            "image_url": "https://example.com/business-card.jpg",
            "is_active": True,
        },
        {
            "sku": "VFW-1003",
            "name": "Packaging Tape",
            "description": "Heavy-duty packaging tape roll",
            "unit_price": Decimal("149.00"),
            "quantity_available": 18,
            "image_url": "https://example.com/tape.jpg",
            "is_active": True,
        },
    ]
    existing_skus = {row.sku for row in db.query(Product.sku).filter(Product.sku.in_([item["sku"] for item in default_products])).all()}
    missing_products = [
        Product(
            sku=item["sku"],
            name=item["name"],
            description=item["description"],
            unit_price=item["unit_price"],
            quantity_available=item["quantity_available"],
            image_url=item["image_url"],
            is_active=item["is_active"],
        )
        for item in default_products
        if item["sku"] not in existing_skus
    ]
    if missing_products:
        db.add_all(missing_products)
        db.commit()

    if ADMIN_USERNAME and ADMIN_PASSWORD and not db.query(AdminUser).filter(AdminUser.username == ADMIN_USERNAME).one_or_none():
        db.add(AdminUser(username=ADMIN_USERNAME, password_hash=hash_password(ADMIN_PASSWORD), role="admin"))
        db.commit()


def initialize_app_state() -> None:
    try:
        from dev.db import init_db

        init_db()
    except Exception:
        logger.exception("Database initialization failed during startup")
    with next(app_db.get_db()) as db:
        ensure_seed_data(db)


initialize_app_state()


@app.on_event("startup")
def startup_event() -> None:
    initialize_app_state()


@app.get("/")
def home() -> Dict[str, object]:
    return {
        "company": DEFAULT_SITE_SETTINGS["company_name"],
        "tagline": DEFAULT_SITE_SETTINGS["tagline"],
        "status": "ok",
        "message": "Vinayaka File Works storefront API is running.",
    }


@app.get("/api/site-settings", response_model=schemas.SiteSettingsOut)
def get_site_settings() -> schemas.SiteSettingsOut:
    return schemas.SiteSettingsOut(**DEFAULT_SITE_SETTINGS)


@app.get("/api/products", response_model=List[schemas.ProductOut])
def list_products(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)) -> List[schemas.ProductOut]:
    rows = db.query(Product).filter(Product.is_active.is_(True)).offset(skip).limit(limit).all()
    return [
        schemas.ProductOut(
            id=r.id,
            sku=r.sku,
            name=r.name,
            description=r.description,
            unit_price=float(r.unit_price),
            quantity_available=r.quantity_available,
            image_url=r.image_url,
        )
        for r in rows
    ]


@app.get("/api/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)) -> schemas.ProductOut:
    product = db.query(Product).filter(Product.id == product_id).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return schemas.ProductOut(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        unit_price=float(product.unit_price),
        quantity_available=product.quantity_available,
        image_url=product.image_url,
    )


@app.post("/api/cart", response_model=schemas.CartSummaryOut)
def cart_summary(payload: schemas.CartRequest, db: Session = Depends(get_db)) -> schemas.CartSummaryOut:
    items: List[schemas.CartLineOut] = []
    subtotal = Decimal("0.00")
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).one_or_none()
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product not found: {item.product_id}")
        line_total = Decimal(str(product.unit_price)) * item.quantity
        subtotal += line_total
        items.append(
            schemas.CartLineOut(
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                quantity=item.quantity,
                unit_price=float(product.unit_price),
                line_total=float(line_total),
            )
        )
    return schemas.CartSummaryOut(
        items=items,
        subtotal=float(subtotal),
        shipping=0.0,
        total=float(subtotal),
        currency="INR",
    )


@app.post("/api/orders", response_model=schemas.OrderResponse)
def create_order(
    order_in: schemas.OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = None,
) -> schemas.OrderResponse:
    if idempotency_key is None:
        idempotency_key = request.headers.get("Idempotency-Key")
    try:
        result = order_service.create_order(db, order_in, idempotency_key=idempotency_key)
        return schemas.OrderResponse(
            order_id=result["order_id"],
            order_status=result["order_status"],
            payment_status=result["payment_status"],
            total_amount=result["total_amount"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Error creating order")
        raise HTTPException(status_code=500, detail="internal error")


@app.get("/api/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)) -> Dict[str, object]:
    order = db.query(Order).filter(Order.id == order_id).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order.id,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "total_amount": float(order.total_amount),
    }


@app.get("/api/orders/{order_id}/invoice", response_model=schemas.InvoiceResponse)
def get_invoice(order_id: str, db: Session = Depends(get_db)) -> schemas.InvoiceResponse:
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).one_or_none()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    download_url = None
    if (invoice.status or "").upper() == "READY" and invoice.pdf_path:
        download_url = f"file://{invoice.pdf_path}"
    return schemas.InvoiceResponse(invoice_id=invoice.id, status=invoice.status, download_url=download_url)


@app.post("/api/payments/create-session", response_model=schemas.PaymentSessionOut)
def create_payment_session(payload: schemas.PaymentSessionCreate) -> schemas.PaymentSessionOut:
    adapter = payment_adapter.StripeAdapter()
    session_info = adapter.create_session(amount_cents=payload.amount_cents, metadata={"order_id": payload.order_id})
    return schemas.PaymentSessionOut(
        session_id=session_info.get("session_id", "stub_session"),
        url=session_info.get("url"),
        status=session_info.get("status", "stubbed"),
    )


@app.post("/api/payments/webhook")
async def payments_webhook(request: Request) -> Dict[str, str]:
    raw_body = await request.body()
    adapter = payment_adapter.StripeAdapter()
    event = adapter.verify_webhook(raw_body, request.headers.get("Stripe-Signature", ""))
    if event.get("type") == "payment_intent.succeeded":
        return {"status": "ok"}
    return {"status": "unhandled"}


def require_admin(request: Request) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in SESSION_STORE:
        raise HTTPException(status_code=401, detail="Authentication required")
    return SESSION_STORE[session_id]


@app.post("/api/admin/login")
def admin_login(credentials: schemas.AdminLogin, response: Response, db: Session = Depends(get_db)) -> Dict[str, object]:
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail="missing credentials")
    admin = db.query(AdminUser).filter(AdminUser.username == credentials.username).one_or_none()
    if admin is None or not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    session_id = str(uuid.uuid4())
    SESSION_STORE[session_id] = admin.username
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=APP_ENV == "production",
        max_age=3600,
    )
    return {"status": "ok", "username": admin.username, "role": admin.role}


@app.post("/api/admin/logout")
def admin_logout(request: Request, response: Response) -> Dict[str, str]:
    session_id = request.cookies.get("session_id")
    if session_id:
        SESSION_STORE.pop(session_id, None)
    response.delete_cookie("session_id")
    return {"status": "ok"}


@app.get("/api/admin/orders")
def list_admin_orders(db: Session = Depends(get_db), username: str = Depends(require_admin)) -> List[Dict[str, object]]:
    orders = db.query(Order).order_by(Order.order_date.desc()).limit(50).all()
    result: List[Dict[str, object]] = []
    for order in orders:
        result.append(
            {
                "order_id": order.id,
                "customer_name": order.customer.full_name if order.customer else "Walk-in Customer",
                "total_amount": float(order.total_amount),
                "order_status": order.order_status,
                "payment_status": order.payment_status,
            }
        )
    return result


@app.patch("/api/admin/orders/{order_id}/status")
def update_order_status(
    order_id: str,
    payload: schemas.AdminStatusUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(require_admin),
) -> Dict[str, object]:
    order = db.query(Order).filter(Order.id == order_id).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    status = payload.status.strip().upper()
    allowed = {"PENDING", "CONFIRMED", "PROCESSED", "CANCELLED"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported order status")

    order.order_status = status
    if status == "PROCESSED":
        order.payment_status = "PAID"
    db.commit()
    return {"order_id": order.id, "order_status": order.order_status, "message": "status updated"}


@app.get("/api/admin/health")
def admin_health() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("dev.app.main:app", host="0.0.0.0", port=port, reload=True)
