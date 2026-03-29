# Hackathon Platform — Backend API

A full-featured community platform backend for students and universities, covering **internship listings, apartment search, events, a community forum, real-time chat, and AI-powered recommendations** — all secured with Keycloak authentication.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
  - [1. Clone & Configure Environment](#1-clone--configure-environment)
  - [2. Start Docker Services](#2-start-docker-services)
  - [3. Install Python Dependencies](#3-install-python-dependencies)
  - [4. Run Database Migrations](#5-run-database-migrations)
  - [5. Start the API](#6-start-the-api)
  - [6. Seed Demo Data](#7-seed-demo-data)
- [Running with Docker (Full Stack)](#running-with-docker-full-stack)
- [API Overview](#api-overview)
- [Project Structure](#project-structure)

---

## Features

| Module | Highlights |
|--------|-----------|
| **Auth** | Keycloak-backed registration/login, JWT (RS256), Google SSO, 3 roles: `student`, `university`, `admin` |
| **Universities** | CRUD management of university accounts |
| **Student Profiles** | Profile creation and management per student |
| **Internships** | Manual CRUD + auto-sync from Adzuna external API |
| **Apartments** | Listing management + sync from RentCast / demo seed, location filtering |
| **Events** | Full CRUD, RSVP system, banner + gallery image uploads (up to 7 images) |
| **Forum** | Community posts (named or anonymous with cartoon aliases), comments, likes, reports, admin moderation |
| **Chat** | Real-time WebSocket messaging, chat request system, association rooms |
| **Recommendations** | Claude AI-powered personalized internship/apartment recommendations |
| **Dashboard** | Aggregated overview for each user role |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API Framework** | FastAPI 0.111 + Uvicorn (ASGI) |
| **Database** | PostgreSQL 16 |
| **ORM / Migrations** | SQLAlchemy 2 (async) + Alembic |
| **DB Drivers** | asyncpg (async), psycopg2 (Alembic sync) |
| **Identity / Auth** | Keycloak 24 (OpenID Connect, RS256 JWT) |
| **Cache / Broker** | Redis 7 |
| **AI** | Anthropic Claude (via `anthropic` SDK) |
| **Validation** | Pydantic v2 + pydantic-settings |
| **File Handling** | python-multipart, Pillow, PyPDF2, pytesseract |
| **HTTP Client** | httpx (async) |
| **Logging** | structlog (structured JSON logs) |
| **Testing** | pytest, pytest-asyncio, factory-boy, faker |
| **Linting / Types** | ruff, mypy |
| **Containerisation** | Docker + Docker Compose |

---

## Architecture

The project follows **Clean Architecture** with four distinct layers:

```
app/
├── api/            # HTTP layer — FastAPI routers, request/response schemas
├── application/    # Use cases & DTOs — pure business logic, no framework deps
├── domain/         # Entities, repository interfaces, domain exceptions
└── infrastructure/ # DB models, repository implementations, Keycloak client
```

---

## Prerequisites

- **Python 3.11+**
- **Docker Desktop** (for Postgres, Redis, Keycloak)
- **Git**

---

## Local Development Setup

### 1. Clone & Configure Environment

```bash
git clone <your-repo-url>
cd Hackathon

# Copy the example env file
cp .env.example .env          # macOS/Linux
# Copy-Item .env.example .env  # Windows PowerShell

# Generate a secure secret key and paste it into .env as SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

Open `.env` and set `SECRET_KEY` to the generated value. All other defaults work out of the box for local development.

---

### 2. Start Docker Services

```bash
docker compose up -d
```

This starts:

| Service | Port | Purpose |
|---------|------|---------|
| `postgres` | `5432` | Application database |
| `keycloak_db` | `5433` | Keycloak's internal database |
| `keycloak` | `8080` | Identity provider (admin UI) |
| `redis` | `6379` | Cache and WebSocket broker |

Wait ~30 seconds for Keycloak to fully start before proceeding.

```bash
# Check all services are healthy
docker compose ps
```

To stop services (keeps data):
```bash
docker compose down
```

To stop and wipe all data:
```bash
docker compose down -v
```

---

### 3. Install Python Dependencies

```bash
# Create and activate a virtual environment
python -m venv .venv

source .venv/bin/activate          # macOS / Linux
# .\.venv\Scripts\Activate.ps1    # Windows PowerShell

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

### 4. Run Database Migrations

```bash
python -m alembic upgrade head
```

To check the current migration status:
```bash
python -m alembic current
```

To check for multiple heads (should only show one after a clean setup):
```bash
python -m alembic heads
```

---

### 5. Start the API

```bash
python -m uvicorn main:app --reload
```

The API is now available at:

| URL | Description |
|-----|-------------|
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI (interactive docs) |
| [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | ReDoc documentation |
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Health check |
| [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) | OpenAPI schema |

---

### 6. Seed Demo Data

To populate 70 realistic events with banner and gallery images:

```bash
# Make sure your DATABASE_URL is set in .env, then run:
psql $DATABASE_URL -f seed_events.sql
```

> **Note:** Images use `picsum.photos` with deterministic seeds — no API key required. Example banner: `https://picsum.photos/seed/event-1/1200/400`

---

## Running with Docker (Full Stack)

To run the entire stack including the API in Docker (no local Python needed):

```bash
docker compose up --build
```

The API container automatically runs `alembic upgrade head` before starting Uvicorn, so migrations are always applied on startup.

Access the API at [http://localhost:8000/docs](http://localhost:8000/docs).

## Database Migrations

```bash
# Apply all pending migrations
python -m alembic upgrade head

# Roll back one migration
python -m alembic downgrade -1

# Show current applied revision
python -m alembic current

# Show all head revisions (should be exactly 1)
python -m alembic heads

# Auto-generate a new migration after changing models
python -m alembic revision --autogenerate -m "describe your change"
```

**If you encounter `Multiple head revisions`:**
```bash
# Identify the heads
python -m alembic heads

# Create a merge migration
python -m alembic merge -m "merge heads" <head1> <head2>

# Apply
python -m alembic upgrade head
```

---

## Project Structure

```
Hackathon/
├── main.py                          # FastAPI app factory + lifespan
├── alembic.ini                      # Alembic config
├── requirements.txt                 # Pinned dependencies
├── pyproject.toml                   # Project metadata (Poetry)
├── Dockerfile                       # Production container image
├── docker-compose.yml               # Local dev services
├── .env.example                     # Environment variable template
├── seed_events.sql                  # Demo data seed script (70 events)
│
├── keycloak/
│   └── realm-export.json            # Pre-configured Keycloak realm
│
├── alembic/
│   ├── env.py                       # Migration environment (reads .env)
│   └── versions/                    # 19 migration files
│
└── app/
    ├── api/
    │   ├── dependencies.py          # CurrentUser, AdminUser FastAPI deps
    │   └── v1/
    │       ├── router.py            # Aggregates all sub-routers
    │       ├── chat.py              # WebSocket + chat REST endpoints
    │       └── endpoints/
    │           ├── auth.py
    │           ├── universities.py
    │           ├── student_profiles.py
    │           ├── internships.py
    │           ├── apartments.py
    │           ├── events.py        # Includes image upload endpoints
    │           ├── forum.py         # Posts, comments, likes, reports
    │           ├── recommendations.py
    │           └── dashboard.py
    │
    ├── application/
    │   ├── dto/                     # Data Transfer Objects (Pydantic)
    │   └── use_cases/               # One file per feature / use-case
    │
    ├── domain/
    │   ├── entities/                # Pure Python dataclass entities
    │   ├── repositories/            # Abstract repository interfaces
    │   └── exceptions/              # Domain-level exceptions
    │
    ├── infrastructure/
    │   ├── database/
    │   │   ├── session.py           # Async SQLAlchemy session factory
    │   │   ├── models/              # SQLAlchemy ORM models
    │   │   └── repositories/        # Concrete repository implementations
    │   └── keycloak/
    │       ├── admin_client.py      # Keycloak user management client
    │       └── jwt_validator.py     # RS256 JWT verification via JWKS
    │
    └── core/
        └── config.py                # Pydantic-settings Settings class
```

---

## Quick Start (TL;DR)

```bash
# 1. Setup
cp .env.example .env
# Edit .env — set SECRET_KEY

# 2. Start services
docker compose up -d

# 3. Install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4. Migrate
python -m alembic upgrade head

# 5. Run
python -m uvicorn main:app --reload

# 6. Open docs
open http://127.0.0.1:8000/docs
```
