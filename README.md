# MentalHealth-Hackathon Backend

Local development uses Docker for Postgres and Redis, while the FastAPI app runs on your machine.

## Prerequisites

- Python 3.11
- Docker Desktop

## 1. Create your local env file

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the generated secret into `.env` as `SECRET_KEY`.

## 2. Start local services

```powershell
docker compose up -d
```

This starts:
- Postgres on `localhost:5432`
- Redis on `localhost:6379`

To stop services:

```powershell
docker compose down
```

To stop and remove persisted data:

```powershell
docker compose down -v
```

## 3. Install Python dependencies

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 4. Run database migrations

```powershell
python -m alembic upgrade head
```

## 5. Start the API locally

```powershell
python -m uvicorn main:app --reload
```

Open the docs at `http://127.0.0.1:8000/docs`.

## 6. Basic smoke test flow

Use Swagger UI to test the main backend flow:

1. `POST /api/v1/universities/`
2. `POST /api/v1/student-profiles/` with header `X-User-Id: student-1`
3. `POST /api/v1/internships/` with header `X-User-Id: admin-1`
4. `POST /api/v1/recommendations/generate`
5. `GET /api/v1/recommendations/me` with header `X-User-Id: student-1`

## Environment Defaults

The local Docker stack matches the default `.env.example` values:

- `DATABASE_URL=postgresql+asyncpg://hackathon_user:hackathon_pass@localhost:5432/hackathon_db`
- `DATABASE_SYNC_URL=postgresql+psycopg2://hackathon_user:hackathon_pass@localhost:5432/hackathon_db`
- `REDIS_URL=redis://localhost:6379/0`
