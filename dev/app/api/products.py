"""Product catalog endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dev.app import db as app_db
from dev.app import schemas
from dev.app.models import Product

router = APIRouter()


@router.get("/api/products", response_model=List[schemas.ProductOut])
def list_products(skip: int = 0, limit: int = 50, db: Session = Depends(app_db.get_db)) -> List[schemas.ProductOut]:
    rows = db.query(Product).filter(Product.is_active.is_(True)).offset(skip).limit(limit).all()
    return [
        schemas.ProductOut(
            id=item.id,
            sku=item.sku,
            name=item.name,
            description=item.description,
            unit_price=float(item.unit_price),
            quantity_available=item.quantity_available,
            image_url=item.image_url,
        )
        for item in rows
    ]


@router.get("/api/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: str, db: Session = Depends(app_db.get_db)) -> schemas.ProductOut:
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
