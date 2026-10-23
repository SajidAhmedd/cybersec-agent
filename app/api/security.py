"""
API Security Helpers
Admin authentication for write endpoints
"""

import secrets

from fastapi import Header, HTTPException

from app.config import settings

def require_admin(x_admin_key: str = Header(default="")):
    """
    FastAPI dependency: allow the request only with a valid X-Admin-Key header.
    Admin endpoints are disabled entirely when ADMIN_API_KEY is not set.
    """
    if not settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Admin endpoints are disabled")
    if not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")
