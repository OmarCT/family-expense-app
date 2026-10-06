# services/core

FastAPI + PostgreSQL. Poetry: `poetry install`, `poetry run pytest`, `poetry run ruff check .`, `poetry run mypy .`, `poetry run alembic upgrade head`.

- Arrancar la API: `AUTH0_DOMAIN=... AUTH0_AUDIENCE=... poetry run uvicorn --factory fea_core.main:create_app`. Sin esas variables falla al arrancar (a propósito). Los endpoints deben coincidir con `contracts/openapi.yaml`; una prueba lo comprueba.
- Reglas de dinero en `src/fea_core/money/` (enteros en centavos). Deben pasar `testvectors/*.json`; no cambies una regla sin añadir primero el vector.
- Cada endpoint de escritura: client ID obligatorio (idempotencia), revisión base en ediciones (409 con la revisión actual), evento en el outbox **en la misma transacción**.
- Contexto RLS: `SET LOCAL app.user_id/app.household_id` al abrir la transacción; el rol de la app no es dueño de las tablas y no tiene `BYPASSRLS`.
- Migraciones Alembic: nunca editar una ya aplicada. Cada tabla nueva con su política RLS y su prueba de frontera.
- Auth0: validar JWT detrás de `TokenVerifier`; sin PII en logs.
- Tests con `hypothesis` para los invariantes del CLAUDE.md raíz; marca `@pytest.mark.integration` los que necesiten PostgreSQL.
