---
name: Project Overview
description: FastAPI hackathon project - internship matching platform with Keycloak auth
type: project
---

FastAPI backend for a student internship matching platform. Clean architecture (domain/application/infrastructure/api layers).

**Stack:** FastAPI, PostgreSQL (asyncpg), SQLAlchemy 2 async, Alembic, Redis, Keycloak 24 for auth, httpx, python-jose.

**Auth:** Keycloak handles identity. Three roles: student, university, admin. Google SSO configured via Keycloak IDP. JWT validation uses RS256 JWKS endpoint.

**Key tables:** universities (has keycloak_user_id FK to Keycloak sub), student_profiles (user_id = Keycloak sub), internships, internship_recommendations.

**Auth endpoints:** POST /api/v1/auth/register/student|university|admin, POST /api/v1/auth/login, POST /api/v1/auth/refresh, GET /api/v1/auth/google/url, GET /api/v1/auth/me

**Dashboard endpoints:** GET /api/v1/dashboard/student|university|admin (role-gated)

**Why:** Hackathon project — speed matters, Keycloak centralizes auth so we don't manage passwords.
**How to apply:** Check existing patterns before suggesting changes; the architecture is intentionally clean/layered.
