# Family Expense App

App de gastos del hogar (móvil + web) con captura offline-first, splits por ítem entre usuarios y grupos, ledger por pares, analítica, historial de precios y presupuestos. Diseñada como sistema distribuido a propósito. Plan completo: @docs/specs/implementation-plan.md · Arquitectura: @docs/ARCHITECTURE.md

## Estado actual
Se trabaja por slices verticales (0 → 5). Slice activo: **0 — Foundations**. Actualiza `docs/ROADMAP.md` al cerrar cada punto. No adelantes trabajo de slices posteriores.

## Stack
- Clientes: React Native con **Expo + dev client** (`apps/mobile`), React web (`apps/web`), TypeScript estricto
- Paquetes TS: `packages/domain` (reglas de dinero, unidades), `packages/sync-client`
- Servicios Python 3.12: `services/core` (FastAPI + PostgreSQL + RLS), `services/workers` (consumidores). **Gestor de dependencias: Poetry** (nunca pip/requirements.txt)
- Contrato: `contracts/openapi.yaml` → cliente TS generado
- Nube: **AWS** (ECS Fargate, RDS PostgreSQL con PITR, SQS FIFO/SNS, S3, Secrets Manager). Auth: **Auth0**
- Node con **pnpm** workspaces; IaC en `infra/` (Terraform)

## Comandos
```bash
make up            # docker compose: 2 PostgreSQL, LocalStack (SQS/S3)
make test          # todo: Python + TS + vectores compartidos
make vectors       # SOLO vectores de dinero en Python y TypeScript
make lint          # ruff + mypy + eslint + tsc
make api-gen       # regenera cliente TS desde openapi.yaml
# Python (desde services/core o services/workers)
poetry install
poetry run pytest
poetry run ruff check . && poetry run mypy .
poetry run alembic upgrade head
# TypeScript (raíz)
pnpm install && pnpm -r test
```

## Reglas inviolables
1. **Dinero**: enteros en centavos (`int`), nunca `float`/`Decimal` en el wire ni en TS `number` con fracciones. Una sola regla de redondeo (largest remainder, desempate por hash). Todo cambio de reglas empieza en `testvectors/` y debe pasar en Python **y** TypeScript.
2. **Ledger append-only**: gastos = revisiones inmutables; borrar = tombstone; liquidaciones/reversos/perdones = entradas. Nunca `UPDATE`/`DELETE` sobre datos del ledger ni sobre eventos almacenados.
3. **Servidor = fuente de verdad**. El teléfono encola escrituras y nunca fusiona. Offline es solo *alta* (add-only).
4. **Visibilidad en tres capas**: en el evento, en RLS de PostgreSQL y en los filtros del feed/proyectores. Un gasto "solo participantes" jamás llega a un no participante, ni como tombstone.
5. **Idempotencia**: toda escritura lleva client ID; el reintento devuelve el resultado original. Consumidores idempotentes por event ID.
6. **Eventos versionados**: campo `schema_version`; cambios aditivos por defecto, upcasters para los rotos. Versión desconocida → el consumidor se detiene y alerta.
7. **Sin datos personales en logs**; correlation ID en cada salto.
8. **i18n**: ninguna cadena visible en código; claves de traducción, `es-MX` primero.
9. No agregar dependencias sin avisar. No tocar migraciones ya aplicadas: crear una nueva.
10. Secretos nunca en el repo: `.env.example` solo con placeholders.

## Convenciones
- Python: type hints obligatorios, `ruff` + `mypy --strict`, tests con `pytest` + `hypothesis` para invariantes. SQLAlchemy 2 + psycopg 3, Alembic para migraciones.
- TS: `strict`, sin `any`; ESLint + Prettier; tests con Vitest.
- Contrato primero: cambia `openapi.yaml`, regenera, luego implementa. Cambios aditivos dentro de `/v1`.
- Commits convencionales (`feat:`, `fix:`, `docs:`...). Una decisión de arquitectura nueva → ADR en `docs/decisions/` (usa `/new-adr`).
- Cada slice termina con tests que prueban sus invariantes; no marques un punto del roadmap como hecho sin ellos.

## Invariantes que deben cumplirse siempre (property-based)
- Los shares de un ítem suman exactamente su total; los extras asignados suman los extras del ticket
- Los balances de un hogar suman cero
- Reintentar una escritura con el mismo client ID no duplica
- Gasto participants-only nunca se devuelve a un no participante

## Dónde está cada cosa
- `docs/decisions/` ADRs · `docs/specs/` plan y specs · `docs/ROADMAP.md` checklist por slice
- `services/core/CLAUDE.md`, `services/workers/CLAUDE.md`, `packages/domain/CLAUDE.md`: reglas por módulo
- `.claude/commands/`, `.claude/agents/`: comandos y subagentes del proyecto
