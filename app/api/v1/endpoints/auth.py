from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminUser, get_current_user
from app.application.dto.student_profile_dto import CreateStudentProfileDTO
from app.application.dto.university_dto import CreateUniversityDTO
from app.application.use_cases.create_student_profile import CreateStudentProfileUseCase
from app.application.use_cases.create_university import CreateUniversityUseCase
from app.core.config import get_settings
from app.domain.exceptions.student_profile import StudentProfileAlreadyExistsError
from app.domain.exceptions.university import UniversityAlreadyExistsError
from app.infrastructure.database.repositories.student_profile_repository_impl import (
    SQLAlchemyStudentProfileRepository,
)
from app.infrastructure.database.repositories.university_repository_impl import (
    SQLAlchemyUniversityRepository,
)
from app.infrastructure.database.session import get_async_session
from app.infrastructure.keycloak import admin_client as kc
from app.infrastructure.keycloak.admin_client import KeycloakAdminError

router = APIRouter(prefix="/auth", tags=["Auth"])

_settings = get_settings()

DbSession = Annotated[AsyncSession, Depends(get_async_session)]


# ── Request / Response schemas ────────────────────────────────────────────────


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class StudentRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    university_id: str
    major: str = Field(..., min_length=1, max_length=255)
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    graduation_year: int | None = None
    preferred_locations: list[str] = Field(default_factory=list)


class UniversityRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    contact_name: str = Field(..., min_length=1, max_length=200)
    university_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=1, max_length=100)


class AdminRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    registration_secret: str


class GoogleSSOUrlResponse(BaseModel):
    url: str


# ── Helpers ───────────────────────────────────────────────────────────────────


def _token_response(raw: dict) -> TokenResponse:
    return TokenResponse(
        access_token=raw["access_token"],
        refresh_token=raw.get("refresh_token", ""),
        token_type=raw.get("token_type", "Bearer"),
        expires_in=raw.get("expires_in", 3600),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/register/student",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
async def register_student(
    body: StudentRegisterRequest,
    session: DbSession,
) -> TokenResponse:
    """
    1. Create Keycloak user with the **student** role.
    2. Create a student profile linked to the provided university.
    3. Return access + refresh tokens so the client is immediately logged in.
    """
    # Create Keycloak user
    try:
        keycloak_id = await kc.create_user(
            email=body.email,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
        )
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=exc.status if exc.status in (400, 409) else 502, detail=str(exc))

    # Assign role
    try:
        await kc.assign_realm_role(keycloak_id, "student")
    except KeycloakAdminError as exc:
        await kc.delete_user(keycloak_id)
        raise HTTPException(status_code=502, detail=f"Role assignment failed: {exc}")

    # Create student profile
    repo = SQLAlchemyStudentProfileRepository(session)
    try:
        dto = CreateStudentProfileDTO(
            user_id=keycloak_id,
            university_id=body.university_id,
            major=body.major,
            skills=body.skills,
            interests=body.interests,
            graduation_year=body.graduation_year,
            preferred_locations=body.preferred_locations,
        )
        await CreateStudentProfileUseCase(repo).execute(dto)
    except StudentProfileAlreadyExistsError:
        pass  # idempotent — profile might already exist if retrying
    except Exception as exc:
        await kc.delete_user(keycloak_id)
        raise HTTPException(status_code=500, detail=f"Profile creation failed: {exc}")

    # Return tokens
    try:
        raw = await kc.get_tokens(body.email, body.password)
        return _token_response(raw)
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/register/university",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new university account",
)
async def register_university(
    body: UniversityRegisterRequest,
    session: DbSession,
) -> TokenResponse:
    """
    1. Create a Keycloak user with the **university** role.
    2. Create a university record linked to this Keycloak user.
    3. Return access + refresh tokens.
    """
    first, _, last = body.contact_name.partition(" ")

    try:
        keycloak_id = await kc.create_user(
            email=body.email,
            password=body.password,
            first_name=first,
            last_name=last or first,
        )
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=exc.status if exc.status in (400, 409) else 502, detail=str(exc))

    try:
        await kc.assign_realm_role(keycloak_id, "university")
    except KeycloakAdminError as exc:
        await kc.delete_user(keycloak_id)
        raise HTTPException(status_code=502, detail=f"Role assignment failed: {exc}")

    uni_repo = SQLAlchemyUniversityRepository(session)
    try:
        dto = CreateUniversityDTO(
            name=body.university_name,
            domain=body.domain,
            country=body.country,
            requesting_user_id=keycloak_id,
            keycloak_user_id=keycloak_id,
        )
        await CreateUniversityUseCase(uni_repo).execute(dto)
    except UniversityAlreadyExistsError as exc:
        await kc.delete_user(keycloak_id)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        await kc.delete_user(keycloak_id)
        raise HTTPException(status_code=500, detail=f"University creation failed: {exc}")

    try:
        raw = await kc.get_tokens(body.email, body.password)
        return _token_response(raw)
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/register/admin",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new admin account (requires admin registration secret)",
)
async def register_admin(body: AdminRegisterRequest) -> TokenResponse:
    """
    Protected by a server-side secret (`ADMIN_REGISTRATION_SECRET` env var).
    Creates a Keycloak user with the **admin** role.
    """
    if body.registration_secret != _settings.admin_registration_secret:
        raise HTTPException(status_code=403, detail="Invalid admin registration secret.")

    try:
        keycloak_id = await kc.create_user(
            email=body.email,
            password=body.password,
            first_name=body.first_name,
            last_name=body.last_name,
        )
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=exc.status if exc.status in (400, 409) else 502, detail=str(exc))

    try:
        await kc.assign_realm_role(keycloak_id, "admin")
    except KeycloakAdminError as exc:
        await kc.delete_user(keycloak_id)
        raise HTTPException(status_code=502, detail=f"Role assignment failed: {exc}")

    try:
        raw = await kc.get_tokens(body.email, body.password)
        return _token_response(raw)
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(body: LoginRequest) -> TokenResponse:
    """Exchange email/password for Keycloak access + refresh tokens."""
    try:
        raw = await kc.get_tokens(body.email, body.password)
        return _token_response(raw)
    except KeycloakAdminError as exc:
        code = status.HTTP_401_UNAUTHORIZED if exc.status == 401 else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(status_code=code, detail=str(exc))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an access token",
)
async def refresh(body: RefreshRequest) -> TokenResponse:
    """Exchange a refresh token for a new access token."""
    try:
        raw = await kc.refresh_tokens(body.refresh_token)
        return _token_response(raw)
    except KeycloakAdminError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get(
    "/google/url",
    response_model=GoogleSSOUrlResponse,
    summary="Get Google SSO redirect URL",
)
async def google_sso_url(request: Request) -> GoogleSSOUrlResponse:
    """
    Returns the Keycloak URL to redirect the user to for Google sign-in.
    After authentication Keycloak will redirect back to the `redirect_uri`
    with an auth code that can be exchanged for tokens.

    The URL uses the same host/port that the browser used to reach this API
    so it works correctly behind Docker port-mapping or a reverse proxy.
    """
    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/v1/auth/google/callback"
    # Build a public-facing Keycloak URL using the same host as the API request
    public_kc_url = f"{request.url.scheme}://{request.url.netloc.split(':')[0]}:8080"
    return GoogleSSOUrlResponse(url=kc.google_sso_url(redirect_uri, public_kc_url))


@router.get(
    "/me",
    summary="Get current authenticated user info",
)
async def me(claims=Depends(get_current_user)) -> dict:
    """Returns basic info about the currently authenticated user."""
    return {
        "id": claims.sub,
        "email": claims.email,
        "first_name": claims.first_name,
        "last_name": claims.last_name,
        "roles": claims.roles,
    }
