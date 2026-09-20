"""Site settings API for storefront branding and company info."""

from fastapi import APIRouter

router = APIRouter()

SITE_SETTINGS = {
    "company_name": "Vinayaka File Works",
    "tagline": "Print, packaging and stationery for everyday business",
    "phone": "+91 98765 43210",
    "email": "hello@vinayakafileworks.com",
    "address": "7A Market Road",
    "city": "Bengaluru",
    "state": "Karnataka",
    "pincode": "560001",
}


@router.get("/api/site-settings")
def get_site_settings():
    return SITE_SETTINGS
