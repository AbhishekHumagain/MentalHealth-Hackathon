"""Keycloak Admin REST API client using httpx.

Admin operations (create/delete users, assign roles) use the master realm
admin user (KEYCLOAK_ADMIN / KEYCLOAK_ADMIN_PASSWORD) which always has full
access to all realms.  Token issuance and refresh for end-users use the
hackathon realm's own token endpoint.
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings

_settings = get_settings()

# Admin API always targets the hackathon realm
_BASE = f"{_settings.keycloak_url}/admin/realms/{_settings.keycloak_realm}"

# Master realm token endpoint – gives full admin access across all realms
_MASTER_TOKEN_URL = f"{_settings.keycloak_url}/realms/master/protocol/openid-connect/token"

# Hackathon realm token endpoint – used for user login/refresh
_TOKEN_URL = (
    f"{_settings.keycloak_url}/realms/{_settings.keycloak_realm}"
    "/protocol/openid-connect/token"
)


class KeycloakAdminError(Exception):
    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        super().__init__(detail)


async def _get_admin_token(client: httpx.AsyncClient) -> str:
    """Obtain a master-realm admin token (username + password grant)."""
    resp = await client.post(
        _MASTER_TOKEN_URL,
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": _settings.keycloak_admin_user,
            "password": _settings.keycloak_admin_password,
        },
    )
    if resp.status_code != 200:
        raise KeycloakAdminError(resp.status_code, f"Admin token error: {resp.text}")
    return resp.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── Public helpers ────────────────────────────────────────────────────────────


async def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> str:
    """Create a Keycloak user and return their sub (UUID string)."""
    async with httpx.AsyncClient() as client:
        token = await _get_admin_token(client)

        resp = await client.post(
            f"{_BASE}/users",
            headers=_auth(token),
            json={
                "username": email,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": True,
                "credentials": [
                    {
                        "type": "password",
                        "value": password,
                        "temporary": False,
                    }
                ],
            },
        )

        if resp.status_code == 409:
            raise KeycloakAdminError(409, "Email already registered.")
        if resp.status_code not in (200, 201):
            raise KeycloakAdminError(resp.status_code, f"Create user failed: {resp.text}")

        # Keycloak returns the new user URL in Location header
        location = resp.headers.get("Location", "")
        user_id = location.rstrip("/").split("/")[-1]
        if not user_id:
            raise KeycloakAdminError(500, "Could not extract user ID from Keycloak response.")
        return user_id


async def assign_realm_role(user_id: str, role_name: str) -> None:
    """Assign a realm-level role to a user."""
    async with httpx.AsyncClient() as client:
        token = await _get_admin_token(client)

        # Fetch the role representation
        role_resp = await client.get(
            f"{_BASE}/roles/{role_name}",
            headers=_auth(token),
        )
        if role_resp.status_code == 404:
            raise KeycloakAdminError(404, f"Role '{role_name}' not found in realm.")
        if role_resp.status_code != 200:
            raise KeycloakAdminError(role_resp.status_code, f"Get role error: {role_resp.text}")

        role = role_resp.json()

        # Assign the role
        assign_resp = await client.post(
            f"{_BASE}/users/{user_id}/role-mappings/realm",
            headers=_auth(token),
            json=[role],
        )
        if assign_resp.status_code not in (200, 204):
            raise KeycloakAdminError(
                assign_resp.status_code,
                f"Assign role failed: {assign_resp.text}",
            )


async def delete_user(user_id: str) -> None:
    """Delete a Keycloak user (used for cleanup on registration errors)."""
    async with httpx.AsyncClient() as client:
        token = await _get_admin_token(client)
        await client.delete(f"{_BASE}/users/{user_id}", headers=_auth(token))


async def get_tokens(email: str, password: str) -> dict:
    """Exchange credentials for Keycloak access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": _settings.keycloak_client_id,
                "client_secret": _settings.keycloak_client_secret,
                "username": email,
                "password": password,
            },
        )
        if resp.status_code == 401:
            raise KeycloakAdminError(401, "Invalid credentials.")
        if resp.status_code != 200:
            raise KeycloakAdminError(resp.status_code, f"Login failed: {resp.text}")
        return resp.json()


async def refresh_tokens(refresh_token: str) -> dict:
    """Refresh an access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": _settings.keycloak_client_id,
                "client_secret": _settings.keycloak_client_secret,
                "refresh_token": refresh_token,
            },
        )
        if resp.status_code == 400:
            raise KeycloakAdminError(400, "Invalid or expired refresh token.")
        if resp.status_code != 200:
            raise KeycloakAdminError(resp.status_code, f"Token refresh failed: {resp.text}")
        return resp.json()


def google_sso_url(redirect_uri: str, public_keycloak_url: str | None = None) -> str:
    """Return the Keycloak URL that initiates Google SSO.

    ``public_keycloak_url`` overrides the server-side ``KEYCLOAK_URL`` when
    the browser needs a publicly reachable URL (e.g. localhost vs. container
    hostname).  Falls back to ``KEYCLOAK_URL`` if not provided.
    """
    from urllib.parse import urlencode

    base_url = public_keycloak_url or _settings.keycloak_url
    params = urlencode(
        {
            "client_id": "hackathon-frontend",
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid profile email roles",
            "kc_idp_hint": "google",
        }
    )
    base = f"{base_url}/realms/{_settings.keycloak_realm}/protocol/openid-connect/auth"
    return f"{base}?{params}"
