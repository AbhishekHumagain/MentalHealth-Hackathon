FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (.dockerignore excludes .env, __pycache__, etc.)
COPY . .

# Railway injects PORT; fall back to 8000 for local Docker runs
ENV PORT=8000

# Run Alembic migrations then start Uvicorn
# DATABASE_URL must be provided by the platform (Railway / docker-compose env)
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
