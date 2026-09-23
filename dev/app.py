"""Legacy Flask entrypoint (deprecated).

VNK-VNK-1-ENH-001
This repository previously had two competing storefront "home" experiences:
- FastAPI monolith (canonical) running on :8000
- Flask app (legacy) running on :5000

To avoid end-user confusion and enforce a single canonical storefront entry,
Flask GET / redirects users to the FastAPI storefront UI.

Configure via:
- STOREFRONT_BASE_URL (default: http://localhost:8000)

Safety:
- If STOREFRONT_BASE_URL is unset/invalid, default to localhost.
- Always redirect to <base>/storefront/.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

from flask import Flask, redirect

app = Flask(__name__)

# Ensure repo root is on sys.path when running the script directly (e.g., python dev/app.py)
# This helps importing dev.* packages when Python sets sys.path[0] to the script directory.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)


def _safe_storefront_url() -> str:
    base = os.getenv("STOREFRONT_BASE_URL", "http://localhost:8000").strip()
    if not base:
        base = "http://localhost:8000"

    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        # Fall back to safe local default.
        base = "http://localhost:8000"

    return base.rstrip("/") + "/storefront/"


@app.route("/")
def index():
    # 302 redirect keeps developer ergonomics and prevents conflicting landing pages.
    return redirect(_safe_storefront_url(), code=302)


# Register API blueprints if available (register individually so one failing import doesn't disable others)
for _mod in ["products", "cart", "orders", "admin", "invoices", "quote_requests"]:
    try:
        if _mod == "products":
            from dev.api.products import products_bp as bp
        elif _mod == "cart":
            from dev.api.cart import cart_bp as bp
        elif _mod == "orders":
            from dev.api.orders import orders_bp as bp
        elif _mod == "admin":
            from dev.api.admin import admin_bp as bp
        elif _mod == "invoices":
            from dev.api.invoices import invoices_bp as bp
        elif _mod == "quote_requests":
            from dev.api.quote_requests import quote_bp as bp
        else:
            bp = None

        if bp is not None:
            app.register_blueprint(bp)
    except Exception:
        pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
