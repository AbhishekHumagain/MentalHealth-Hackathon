"""Validates Keycloak-issued RS256 JWTs and extracts user claims.

The JWKS URL is computed lazily (inside _get_jwks) so that the KEYCLOAK_URL
environment variable is always read at call time — not at import time.
This prevents 'UnsupportedProtocol' errors when env vars aren't available
during module import (e.g. on Railway cold starts).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import httpx
from jose import JWTError, jwt

from app.core.config import get_settings

# Simple in-process JWKS cache (refresh every 10 minutes)
_jwks_cache: dict = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 600  # seconds


@dataclass
class TokenClaims:
    sub: str  # Keycloak user ID
    email: str
    roles: list[str] = field(default_factory=list)
    first_name: str = ""
    last_name: str = ""


class TokenValidationError(Exception):
    pass


def _jwks_url() -> str:
    """Build the JWKS URL fresh from current settings (lazy — no module-level constant)."""
    s = get_settings()
    base = s.keycloak_url.rstrip("/")
    return f"{base}/realms/{s.keycloak_realm}/protocol/openid-connect/certs"


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache

    url = _jwks_url()
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise TokenValidationError(
                f"Unable to fetch Keycloak JWKS from {url} (HTTP {resp.status_code})."
            )
        _jwks_cache = resp.json()
        _jwks_fetched_at = now
        return _jwks_cache


async def validate_token(token: str) -> TokenClaims:
    """Validate a Bearer token and return structured claims."""
    jwks = await _get_jwks()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise TokenValidationError(f"Invalid token: {exc}") from exc

    sub = payload.get("sub", "")
    email = payload.get("email", payload.get("preferred_username", ""))
    realm_access = payload.get("realm_access", {})
    roles: list[str] = realm_access.get("roles", [])

    return TokenClaims(
        sub=sub,
        email=email,
        roles=roles,
        first_name=payload.get("given_name", ""),
        last_name=payload.get("family_name", ""),
    )
