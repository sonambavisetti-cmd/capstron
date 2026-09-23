"""FastAPI UI routes for the storefront (server-rendered).

VNK-VNK-1-ENH-001
- Consolidate dual UI entrypoints into a single consistent storefront entry.
- Canonical storefront homepage is served by FastAPI at GET / (200 OK).

The legacy Flask entrypoint (dev/app.py) is deprecated and should redirect users
here.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="dev/templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def storefront_home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("storefront/home.html", {"request": request})
