"""Admin bearer-token utilities (VNK-VNK-2-ENH-009).

Scope:
- Issue signed, stateless bearer tokens for admin login.
- Verify token on every request to /api/admin/* endpoints.

Design decisions (from approved design summary):
- Token transport: Authorization: Bearer <token>
- Token TTL: 7 days (exp claim)
- No refresh tokens / revocation list in this iteration.

Implementation notes:
- Uses itsdangerous (already a transitive dependency of Flask) to avoid adding
  new dependencies.
- SECRET_KEY must be configured (env var SECRET_KEY). In development, we allow
  a weak default to preserve developer experience, but production should set a
  strong value.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer

TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
TOKEN_SALT = "admin-auth"  # constant salt; rotate by changing SECRET_KEY


def _get_secret_key() -> str:
    # Keep behavior consistent with existing app approach: rely on env.
    # Provide a dev fallback so local runs don't crash unexpectedly.
    return os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") or "dev-insecure-secret-key"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(_get_secret_key(), salt=TOKEN_SALT)


@dataclass(frozen=True)
class TokenPayload:
    sub: str  # admin username
    iat: int
    exp: int

    def to_dict(self) -> Dict[str, Any]:
        return {"sub": self.sub, "iat": self.iat, "exp": self.exp}


def create_admin_access_token(username: str, now: Optional[int] = None) -> str:
    """Create a signed bearer token for an admin user."""
    issued_at = int(time.time() if now is None else now)
    payload = TokenPayload(sub=username, iat=issued_at, exp=issued_at + TOKEN_TTL_SECONDS)
    return _serializer().dumps(payload.to_dict())


def verify_admin_access_token(token: str, now: Optional[int] = None) -> Dict[str, Any]:
    """Verify a signed bearer token.

    Returns the decoded payload dict.

    Raises ValueError for invalid/expired tokens.
    """
    current = int(time.time() if now is None else now)
    try:
        payload = _serializer().loads(token, max_age=TOKEN_TTL_SECONDS)
    except BadTimeSignature as exc:
        raise ValueError("invalid token") from exc
    except BadSignature as exc:
        raise ValueError("invalid token") from exc

    if not isinstance(payload, dict) or "sub" not in payload:
        raise ValueError("invalid token")

    exp = payload.get("exp")
    if exp is None or not isinstance(exp, int):
        raise ValueError("invalid token")
    if current >= exp:
        raise ValueError("token expired")

    return payload


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip(), parts[1].strip()
    if scheme.lower() != "bearer" or not token:
        return None
    return token
