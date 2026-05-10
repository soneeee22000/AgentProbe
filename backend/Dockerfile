FROM python:3.10-slim

WORKDIR /app

# System deps (gcc for any C-extension wheels that aren't prebuilt).
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Dependency manifests first so the install layer caches across code edits.
COPY pyproject.toml ./
COPY requirements.txt ./

# Source layout has to exist before `pip install -e .` resolves the package.
COPY src/ ./src/

RUN pip install --no-cache-dir -e .

# Application code, migrations, and demo seed scripts. alembic.ini and
# alembic/ are required for the start-up `alembic upgrade head` to succeed.
COPY main.py ./
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/

# Workspace directory for the read_file tool.
RUN mkdir -p /app/workspace

EXPOSE 8000

# Just uvicorn — table creation happens via the FastAPI lifespan
# (Base.metadata.create_all). Run migrations and seed manually after first
# deploy if needed: `railway run python -m scripts.seed_demo_runs`.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
