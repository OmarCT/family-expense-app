FROM python:3.12-slim AS builder
ENV POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_NO_INTERACTION=1 PIP_NO_CACHE_DIR=1
RUN pip install "poetry>=2.0,<3.0"
WORKDIR /app
COPY pyproject.toml poetry.lock poetry.toml ./
RUN poetry install --only main --no-root

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src
RUN useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "--factory", "fea_core.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
