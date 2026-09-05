import os
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# ── Configuration ─────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "dev-insecure-secret-change-in-prod")
JWT_ALGORITHM = "HS256"

# When DEV_TRUST_HEADER=1 the old X-User-Id header behaviour is preserved.
# NEVER enable this in production.
_DEV_TRUST_HEADER = os.getenv("DEV_TRUST_HEADER", "0").strip() == "1"

_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    x_user_id: Optional[str] = Header(default=None),
) -> int:
    """
    Resolve the authenticated user ID from the request.

    Production path (DEV_TRUST_HEADER != 1):
        Expects:  Authorization: Bearer <signed-JWT>
        Returns:  user_id (int) extracted from JWT "sub" claim.
        Raises:   HTTP 401 if token is missing or invalid.

    Dev fallback (DEV_TRUST_HEADER=1):
        Falls back to the legacy X-User-Id header (defaults to 1).
        A warning is printed so it's obvious in logs.
        This mode must NEVER be used in production.
    """
    if _DEV_TRUST_HEADER:
        import warnings
        warnings.warn(
            "DEV_TRUST_HEADER is enabled — JWT validation is BYPASSED. "
            "Do NOT use this in production.",
            stacklevel=2,
        )
        try:
            return int(x_user_id) if x_user_id else 1
        except (ValueError, TypeError):
            return 1

    # ── Production: require a valid JWT ──────────────────────────────────────
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — provide Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise ValueError("Missing 'sub' claim")
        return int(user_id_str)
    except (JWTError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
