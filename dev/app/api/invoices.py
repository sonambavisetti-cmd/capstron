"""Invoice API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dev.app import db as app_db
from dev.app import schemas
from dev.app.models import Invoice

router = APIRouter()


@router.get("/api/orders/{order_id}/invoice", response_model=schemas.InvoiceResponse)
def get_invoice(order_id: str, db: Session = Depends(app_db.get_db)) -> schemas.InvoiceResponse:
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).one_or_none()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    download_url = f"file://{invoice.pdf_path}" if (invoice.status or "").upper() == "READY" and invoice.pdf_path else None
    return schemas.InvoiceResponse(invoice_id=invoice.id, status=invoice.status, download_url=download_url)
