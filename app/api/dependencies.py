from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.infrastructure.keycloak.jwt_validator import TokenClaims, TokenValidationError, validate_token

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> TokenClaims:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await validate_token(credentials.credentials)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*roles: str):

    async def _check(claims: Annotated[TokenClaims, Depends(get_current_user)]) -> TokenClaims:
        if not any(r in claims.roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {', '.join(roles)}.",
            )
        return claims

    return _check


# Convenience typed aliases
CurrentUser = Annotated[TokenClaims, Depends(get_current_user)]
StudentUser = Annotated[TokenClaims, Depends(require_role("student"))]
UniversityUser = Annotated[TokenClaims, Depends(require_role("university"))]
AdminUser = Annotated[TokenClaims, Depends(require_role("admin"))]


# Backward-compatible shim: existing endpoints use get_current_user_id
async def get_current_user_id(
    claims: Annotated[TokenClaims, Depends(get_current_user)],
) -> str:
    return claims.sub
