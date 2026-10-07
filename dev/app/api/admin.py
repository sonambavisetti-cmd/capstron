"""Admin API endpoints."""

import os
import uuid
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from dev.app import db as app_db
from dev.app import schemas
from dev.app.auth import verify_password
from dev.app.models import AdminUser, Order

router = APIRouter()
SESSION_STORE: Dict[str, str] = {}
APP_ENV = os.getenv("APP_ENV", "development").lower()


def require_admin(request: Request) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in SESSION_STORE:
        raise HTTPException(status_code=401, detail="Authentication required")
    return SESSION_STORE[session_id]


@router.post("/api/admin/login")
def admin_login(credentials: schemas.AdminLogin, response: Response, db: Session = Depends(app_db.get_db)) -> Dict[str, object]:
    if not credentials.username or not credentials.password:
        raise HTTPException(status_code=400, detail="missing credentials")
    admin = db.query(AdminUser).filter(AdminUser.username == credentials.username).one_or_none()
    if admin is None or not verify_password(credentials.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    session_id = str(uuid.uuid4())
    SESSION_STORE[session_id] = admin.username
    response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="lax", secure=APP_ENV == "production", max_age=3600)
    return {"status": "ok", "username": admin.username, "role": admin.role}


@router.post("/api/admin/logout")
def admin_logout(request: Request, response: Response) -> Dict[str, str]:
    session_id = request.cookies.get("session_id")
    if session_id:
        SESSION_STORE.pop(session_id, None)
    response.delete_cookie("session_id")
    return {"status": "ok"}


@router.get("/api/admin/orders")
def list_admin_orders(db: Session = Depends(app_db.get_db), username: str = Depends(require_admin)) -> List[Dict[str, object]]:
    result: List[Dict[str, object]] = []
    for order in db.query(Order).order_by(Order.order_date.desc()).limit(50).all():
        result.append({
            "order_id": order.id,
            "customer_name": order.customer.full_name if order.customer else "Walk-in Customer",
            "total_amount": float(order.total_amount),
            "order_status": order.order_status,
            "payment_status": order.payment_status,
        })
    return result


@router.patch("/api/admin/orders/{order_id}/status")
def update_order_status(order_id: str, payload: schemas.AdminStatusUpdate, db: Session = Depends(app_db.get_db), username: str = Depends(require_admin)) -> Dict[str, object]:
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


@router.get("/api/admin/health")
def admin_health() -> Dict[str, str]:
    return {"status": "ok"}
