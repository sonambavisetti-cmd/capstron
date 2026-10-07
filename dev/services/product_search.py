from __future__ import annotations
"""Product search and filter service (VNK-2).

Builds parameterised SQLAlchemy queries only; user input is never concatenated
into SQL. LIKE wildcards in user text are escaped.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from dev.models import Product, ProductCustomization, ProductSize

ALLOWED_MATERIALS = ("PVC", "PP", "BOARD")
MAX_QUERY_LENGTH = 100
MAX_TERMS = 10
MAX_FILTER_LENGTH = 64
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


class SearchValidationError(ValueError):
    """Raised for invalid search parameters; maps to HTTP 400."""


@dataclass
class SearchResult:
    items: List[Product]
    total: int
    limit: int
    offset: int
    applied: Dict[str, Any] = field(default_factory=dict)


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _clean(value: Optional[str], name: str) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > MAX_FILTER_LENGTH:
        raise SearchValidationError(f"{name} must be at most {MAX_FILTER_LENGTH} characters")
    return value


class ProductSearchService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(
        self,
        q: Optional[str] = None,
        material: Optional[str] = None,
        size: Optional[str] = None,
        customization: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> SearchResult:
        terms = self._parse_terms(q)
        material_n = self._validate_material(material)
        size_n = _clean(size, "size")
        size_n = size_n.upper() if size_n else None
        custom_n = _clean(customization, "customization")
        custom_n = custom_n.upper() if custom_n else None
        category_n = _clean(category, "category")

        if not isinstance(limit, int) or limit < 1:
            raise SearchValidationError("limit must be an integer between 1 and %d" % MAX_LIMIT)
        limit = min(limit, MAX_LIMIT)
        if not isinstance(offset, int) or offset < 0:
            raise SearchValidationError("offset must be an integer >= 0")

        conditions = [Product.is_active.is_(True)]
        for term in terms:
            pattern = f"%{_escape_like(term.lower())}%"
            conditions.append(
                or_(
                    func.lower(Product.name).like(pattern, escape="\\"),
                    func.lower(func.coalesce(Product.category, "")).like(pattern, escape="\\"),
                    func.lower(func.coalesce(Product.specifications, "")).like(pattern, escape="\\"),
                    func.lower(Product.sku).like(pattern, escape="\\"),
                    func.lower(func.coalesce(Product.material, "")).like(pattern, escape="\\"),
                )
            )
        if material_n:
            conditions.append(func.upper(Product.material) == material_n)
        if category_n:
            conditions.append(func.lower(Product.category) == category_n.lower())
        if size_n:
            conditions.append(
                select(ProductSize.id)
                .where(ProductSize.product_id == Product.id, ProductSize.size == size_n)
                .exists()
            )
        if custom_n:
            conditions.append(
                select(ProductCustomization.id)
                .where(
                    ProductCustomization.product_id == Product.id,
                    ProductCustomization.option == custom_n,
                )
                .exists()
            )

        where = and_(*conditions)
        total = self.session.execute(select(func.count()).select_from(Product).where(where)).scalar_one()
        items = list(
            self.session.execute(
                select(Product).where(where).order_by(Product.name, Product.id).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )
        applied = {
            "q": " ".join(terms) if terms else None,
            "material": material_n,
            "size": size_n,
            "customization": custom_n,
            "category": category_n,
        }
        return SearchResult(items=items, total=int(total), limit=limit, offset=offset, applied=applied)

    def get_filter_options(self) -> Dict[str, List[str]]:
        active = Product.is_active.is_(True)
        materials_present = {
            (m or "").upper()
            for m in self.session.execute(
                select(Product.material).where(active, Product.material.is_not(None)).distinct()
            ).scalars()
        }
        sizes = self.session.execute(
            select(ProductSize.size)
            .join(Product, Product.id == ProductSize.product_id)
            .where(active)
            .distinct()
            .order_by(ProductSize.size)
        ).scalars().all()
        customizations = self.session.execute(
            select(ProductCustomization.option)
            .join(Product, Product.id == ProductCustomization.product_id)
            .where(active)
            .distinct()
            .order_by(ProductCustomization.option)
        ).scalars().all()
        categories = self.session.execute(
            select(Product.category)
            .where(active, Product.category.is_not(None))
            .distinct()
            .order_by(Product.category)
        ).scalars().all()
        return {
            "materials": [m for m in ALLOWED_MATERIALS if m in materials_present],
            "sizes": list(sizes),
            "customizations": list(customizations),
            "categories": list(categories),
        }

    @staticmethod
    def _parse_terms(q: Optional[str]) -> List[str]:
        if q is None:
            return []
        q = q.strip()
        if len(q) > MAX_QUERY_LENGTH:
            raise SearchValidationError(f"q must be at most {MAX_QUERY_LENGTH} characters")
        terms = q.split()
        if len(terms) > MAX_TERMS:
            raise SearchValidationError(f"q may contain at most {MAX_TERMS} search terms")
        return terms

    @staticmethod
    def _validate_material(material: Optional[str]) -> Optional[str]:
        material = _clean(material, "material")
        if material is None:
            return None
        upper = material.upper()
        if upper not in ALLOWED_MATERIALS:
            raise SearchValidationError("material must be one of: " + ", ".join(ALLOWED_MATERIALS))
        return upper
