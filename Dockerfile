# Stage 1 — shared runtime foundation
FROM python:3.14-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
# Copy deps before source so this install layer caches across code changes
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2 — test image (what CI runs); superset of base with tooling + tests
FROM base AS test
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .bandit_baseline.json ./

# Stage 3 — lean deployable (Fargate/ECS); app only, no tests or tooling
FROM base AS runtime
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
