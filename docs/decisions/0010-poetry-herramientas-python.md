# ADR-0010: Poetry y herramientas Python

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
Poetry 2.x (formato `[project]`), Python 3.12, `poetry.lock` versionado. Grupos: principal, `dev` (pytest, hypothesis, ruff, mypy, httpx). FastAPI + Pydantic v2, SQLAlchemy 2 + psycopg 3, Alembic. En imágenes Docker: `poetry install --only main --no-root` en una etapa de build y copia del virtualenv.

## Consecuencias
Se ejecuta todo con `poetry run ...`. Dependencias nuevas con `poetry add` y aviso en el PR.
