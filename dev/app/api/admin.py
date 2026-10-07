"""Admin API endpoints.

VNK-VNK-2-ENH-009: Admin Authorization
- Issue bearer token on login.
- Require Authorization: Bearer <token> for all /api/admin/* endpoints except login.
"""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from dev.app import db as app_db
from dev.app import schemas
from dev.app.auth import verify_password
from dev.app.auth_tokens import (
    TOKEN_TTL_SECONDS,
    create_admin_access_token,
    extract_bearer_token,
    verify_admin_access_token,
)
from dev.app.models import AdminUser, Order

router = APIRouter()


def require_admin(request: Request, db: Session) -> AdminUser:
    token = extract_bearer_token(request.headers.get("Authorization"))
    if not token:
        # Keep existing {error: ...} pattern (FastAPI uses detail by default).
        raise HTTPException(status_code=401, detail={"error": "Authentication required"})

    try:
        payload = verify_admin_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

    username = payload.get("sub")
    admin = db.query(AdminUser).filter(AdminUser.username == username).one_or_none()
    if admin is None:
        # Implementation decision: treat as unauthorized (token subject no longer exists).
        raise HTTPException(status_code=401, detail={"error": "Authentication required"})
    return admin


@router.post("/api/admin/login")
def admin_login(credentials: schemas.AdminLogin, db: Session = Depends(app_db.get_db)) -> Dict[str, object]:
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail={"error": "missing credentials"})

    admin = db.query(AdminUser).filter(AdminUser.username == credentials.username).one_or_none()
    if admin is None or not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(status_code=401, detail={"error": "invalid credentials"})

    token = create_admin_access_token(admin.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_SECONDS,
        "username": admin.username,
        "role": admin.role,
    }


@router.get("/api/admin/orders")
def list_admin_orders(
    request: Request,
    db: Session = Depends(app_db.get_db),
) -> List[Dict[str, object]]:
    _admin = require_admin(request, db)

    result: List[Dict[str, object]] = []
    for order in db.query(Order).order_by(Order.order_date.desc()).limit(50).all():
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


@router.patch("/api/admin/orders/{order_id}/status")
def update_order_status(
    order_id: str,
    payload: schemas.AdminStatusUpdate,
    request: Request,
    db: Session = Depends(app_db.get_db),
) -> Dict[str, object]:
    _admin = require_admin(request, db)

    order = db.query(Order).filter(Order.id == order_id).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "Order not found"})

    status = payload.status.strip().upper()
    allowed = {"PENDING", "CONFIRMED", "PROCESSED", "CANCELLED"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail={"error": "Unsupported order status"})

    order.order_status = status
    if status == "PROCESSED":
        order.payment_status = "PAID"
    db.commit()
    return {"order_id": order.id, "order_status": order.order_status, "message": "status updated"}


@router.get("/api/admin/health")
def admin_health(request: Request, db: Session = Depends(app_db.get_db)) -> Dict[str, str]:
    _admin = require_admin(request, db)
    return {"status": "ok"}
