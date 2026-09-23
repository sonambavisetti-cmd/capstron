"""Helpers for storefront UI rendering.

Kept intentionally small for the MVP.
"""

from __future__ import annotations

from fastapi.templating import Jinja2Templates


def get_templates() -> Jinja2Templates:
    return Jinja2Templates(directory="dev/templates")
