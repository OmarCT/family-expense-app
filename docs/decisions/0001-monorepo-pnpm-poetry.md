# ADR-0001: Monorepo con pnpm (TypeScript) y Poetry (Python)

- Estado: Aceptada
- Fecha: 2026-10-05

## Contexto
Clientes TS y servicios Python comparten contrato, vectores de dinero y CI. Un cambio de reglas debe romper el build en ambos lados a la vez.

## Decisión
Un solo repo. Node con workspaces de **pnpm** (`apps/*`, `packages/*`). Cada servicio Python es un proyecto **Poetry** independiente (`services/core`, `services/workers`), con `poetry.lock` versionado y virtualenv en el proyecto (`virtualenvs.in-project = true`). Contrato en `contracts/`, vectores en `testvectors/`.

## Alternativas descartadas
- Repos separados: los vectores y el contrato se desincronizan.
- pip + requirements.txt: sin lock reproducible ni grupos de dependencias.
- Workspace único de Python (uv/Poetry plugin): innecesario con dos servicios; se reevalúa si aparece una librería Python compartida.

## Consecuencias
Dos gestores de dependencias; el CI instala ambos. Si `workers` necesita código de `core`, se extrae una librería (`libs/ledger-events`) en lugar de importar entre servicios.
