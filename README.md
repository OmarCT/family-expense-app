# Family Expense App

Gastos del hogar con splits por ítem, ledger por pares, captura offline, escaneo de tickets, historial de precios y presupuestos. Monorepo con clientes en TypeScript y servicios en Python.

## Requisitos
- Node 22 + pnpm 9+
- Python 3.12 + [Poetry](https://python-poetry.org/) 2.x
- Docker + Docker Compose
- Terraform (para `infra/`)

## Primeros pasos
```bash
cp .env.example .env
make up                 # PostgreSQL (core + analytics) y LocalStack
pnpm install
(cd services/core && poetry install)
(cd services/workers && poetry install)
make test
```

## Estructura
```
apps/mobile            Expo (React Native) + dev client
apps/web               React web
packages/domain        reglas de dinero y unidades (TS)
packages/sync-client   cola de escrituras, feed y bootstrap
services/core          FastAPI + PostgreSQL + RLS
services/workers       relay del outbox y consumidores
contracts/             openapi.yaml y esquemas de eventos
testvectors/           vectores JSON compartidos Python/TS
infra/                 Terraform (AWS)
docs/                  arquitectura, ADRs, plan, roadmap
```

Lee primero `CLAUDE.md`, `docs/ARCHITECTURE.md` y `docs/ROADMAP.md`.
