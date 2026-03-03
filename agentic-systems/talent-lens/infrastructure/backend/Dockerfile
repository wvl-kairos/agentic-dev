FROM python:3.12-slim

WORKDIR /app

RUN useradd -m -u 1000 appuser

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies
COPY backend/pyproject.toml .
RUN uv sync --no-dev --no-install-project

# Copy application
COPY backend/src/ src/
COPY backend/alembic/ alembic/
COPY backend/alembic.ini .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "talentlens.main:app", "--host", "0.0.0.0", "--port", "8000"]
