from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalise(url: str) -> tuple[str, str]:
    """
    Return ``(scheme_base, rest)`` from any postgres DSN, stripping any
    existing driver suffix so callers can inject the correct one.

    Examples
    --------
    "postgres://u:p@h:5432/db"          → ("postgresql", "//u:p@h:5432/db")
    "postgresql://u:p@h:5432/db"        → ("postgresql", "//u:p@h:5432/db")
    "postgresql+asyncpg://u:p@h:5432/db"→ ("postgresql", "//u:p@h:5432/db")
    "postgresql+psycopg2://..."         → ("postgresql", "//...")
    """
    url = url.replace("postgres://", "postgresql://", 1)
    # e.g. "postgresql+asyncpg" → ["postgresql", "asyncpg"]
    scheme_full, rest = url.split("://", 1)
    scheme_base = scheme_full.split("+")[0]  # strip +driver
    return scheme_base, f"//{rest}"


def _to_asyncpg(url: str) -> str:
    """Convert any postgres DSN to the asyncpg driver format."""
    base, rest = _normalise(url)
    return f"{base}+asyncpg:{rest}"


def _to_psycopg2(url: str) -> str:
    """Convert any postgres DSN to the psycopg2 driver format."""
    base, rest = _normalise(url)
    return f"{base}+psycopg2:{rest}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    app_name: str = Field(default="Hackathon API")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    secret_key: str = Field(..., min_length=32)

    # ── Database ─────────────────────────────────────────────────────────────
    # Railway injects DATABASE_URL as  postgresql://user:pass@host:port/db
    # We normalise it into the two driver-specific URLs automatically.
    # You can still override DATABASE_URL / DATABASE_SYNC_URL explicitly.
    database_url: str = Field(
        default="",
        description="Async PostgreSQL DSN (asyncpg). Auto-derived from DATABASE_URL if blank.",
    )
    database_sync_url: str = Field(
        default="",
        description="Sync PostgreSQL DSN (psycopg2, Alembic). Auto-derived from DATABASE_URL.",
    )
    db_pool_size: int = Field(default=10, ge=1, le=50)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=5)

    # ── File Storage ──────────────────────────────────────────────────────────
    upload_dir: str = Field(default="/tmp/hackathon_uploads")
    max_file_size_mb: int = Field(default=25, ge=1, le=100)
    allowed_mime_types: list[str] = Field(
        default=["application/pdf", "image/jpeg", "image/png", "image/tiff"]
    )

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ── JWT ───────────────────────────────────────────────────────────────────
    access_token_expire_minutes: int = Field(default=60, ge=5)
    algorithm: str = Field(default="HS256")

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # ── Keycloak ──────────────────────────────────────────────────────────────
    # Always include the scheme, e.g. http://keycloak:8080 or https://keycloak.example.com
    keycloak_url: str = Field(default="http://localhost:8080")
    keycloak_realm: str = Field(default="hackathon")
    keycloak_client_id: str = Field(default="hackathon-api")
    keycloak_client_secret: str = Field(default="hackathon-api-secret")
    # Master realm admin — used only for Admin REST API calls (create/delete users)
    keycloak_admin_user: str = Field(default="admin")
    keycloak_admin_password: str = Field(default="admin")
    # Used to protect admin registration endpoint
    admin_registration_secret: str = Field(default="change-me-admin-secret")
    adzuna_app_id: str | None = Field(default=None)
    adzuna_app_key: str | None = Field(default=None)
    adzuna_country: str = Field(default="us")

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = Field(default=["http://localhost:3000"])

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("keycloak_url", mode="before")
    @classmethod
    def normalise_keycloak_url(cls, v: str) -> str:
        """Ensure keycloak_url always has an http(s):// scheme."""
        v = str(v).strip().rstrip("/")
        if v and not v.startswith(("http://", "https://")):
            v = f"http://{v}"
        return v

    @field_validator("allowed_mime_types", "allowed_origins", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    @model_validator(mode="after")
    def normalise_database_urls(self) -> "Settings":
        """
        Accepts any of these environment variable patterns (Railway / local / custom):

          DATABASE_URL=postgresql://...        ← Railway injects this
          DATABASE_URL=postgresql+asyncpg://...
          DATABASE_URL=postgres://...          ← older Railway format

        Derives both driver-specific URLs automatically so you only need to
        set ONE variable in Railway.  If you set DATABASE_URL *and*
        DATABASE_SYNC_URL explicitly, those values are used as-is.
        """
        raw = self.database_url or ""

        if not raw:
            raise ValueError(
                "DATABASE_URL must be set. "
                "On Railway, link the PostgreSQL service to this deployment."
            )

        # If the user supplied a fully-qualified asyncpg URL already, derive sync from it
        if not self.database_sync_url:
            self.database_sync_url = _to_psycopg2(raw)

        # Ensure the async URL has the asyncpg driver
        if "+asyncpg" not in raw and "+psycopg2" not in raw:
            # Raw URL from Railway — normalise to asyncpg
            self.database_url = _to_asyncpg(raw)
        elif "+psycopg2" in raw:
            # Caller set the sync URL as database_url by mistake — fix it
            self.database_url = _to_asyncpg(raw)

        return self

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
