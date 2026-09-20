"""Order-related API endpoints."""

from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from dev.app import db as app_db
from dev.app import schemas
from dev.app.models import Order
from dev.app.services import order_service

router = APIRouter()


@router.post("/api/orders", response_model=schemas.OrderResponse)
def create_order(
    order_in: schemas.OrderCreate,
    request: Request,
    db: Session = Depends(app_db.get_db),
    idempotency_key: Optional[str] = None,
) -> schemas.OrderResponse:
    if idempotency_key is None:
        idempotency_key = request.headers.get("Idempotency-Key")
    try:
        result = order_service.create_order(db, order_in, idempotency_key=idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schemas.OrderResponse(
        order_id=result["order_id"],
        order_status=result["order_status"],
        payment_status=result["payment_status"],
        total_amount=result["total_amount"],
    )


@router.get("/api/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(app_db.get_db)) -> Dict[str, object]:
    order = db.query(Order).filter(Order.id == order_id).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": order.id,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "total_amount": float(order.total_amount),
    }
