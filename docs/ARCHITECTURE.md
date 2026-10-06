# Arquitectura

Resumen de cómo encajan las piezas. El *porqué* de cada decisión está en `docs/decisions/`; el orden de construcción, en `docs/specs/implementation-plan.md`.

## Vista general

```
 Expo app (SQLite: cola + caché)     React web
        │  REST /v1 (client ID = idempotency key)  │
        └──────────────┬──────────────────────────┘
                       ▼
              services/core (FastAPI)
        valida JWT Auth0 → contexto RLS por transacción
                       │  misma transacción
                       ▼
        PostgreSQL core: ledger + outbox (seq por hogar)
                       │
              services/workers: relay
                       ▼
              SNS → SQS FIFO (group = household_id)
        ┌──────────┬──────────┬───────────┬────────────┐
   analytics   budget/alert   notifier   image cleanup
   projector   evaluator
        ▼
 PostgreSQL analytics (read models, price history)
```

## Componentes

| Componente | Responsabilidad |
| --- | --- |
| `apps/mobile` | Captura offline, escáner (ML Kit / Apple Vision vía Expo Modules), cola de escrituras |
| `apps/web` | Entrada online, analítica, precios |
| `packages/domain` | Reglas de dinero y unidades (misma lógica que Python, validada por vectores) |
| `packages/sync-client` | Drena cola, consume el feed, bootstrap, regla de caducidad; sin asumir almacenamiento |
| `services/core` | API, ledger, RLS, balances, feed de cambios, outbox |
| `services/workers` | Relay del outbox + consumidores idempotentes |
| `contracts/` | `openapi.yaml` y esquemas de evento versionados |

## Flujos clave

**Escritura.** El cliente envía `POST` con client ID → el core abre transacción, fija contexto RLS (`SET LOCAL`), inserta revisión + evento en el outbox, confirma. Un reintento con el mismo ID devuelve el resultado guardado.

**Número de secuencia.** Se asigna en el commit, en orden por hogar, para que un cliente nunca se pierda un cambio que confirma tarde (ver ADR-0006).

**Sincronización.** El cliente drena su cola y luego pide "cambios desde N". El push (FCM/APNs/SSE) solo dice "algo cambió". Cursor viejo o hueco grande → descarta caché y hace bootstrap con snapshot sellado en la secuencia S.

**Proyecciones.** Cada consumidor es idempotente por event ID y reconstruible desde el log. La prueba *replay-equality* reconstruye todo y compara con lo vivo.

**Visibilidad.** Capa 1: el evento declara participantes. Capa 2: políticas RLS. Capa 3: filtros en feed y proyectores. Pruebas de frontera como no miembro, miembro removido y no participante.

## Modelo de datos (núcleo)

Hogares y membresías (admin/member) · placeholders reclamables · grupos · categorías · gastos como revisiones inmutables con tombstone · ítems (nombre crudo, total en centavos, cantidad, unidad y unidad base, producto opcional, moneda) · shares por usuario con etiqueta de grupo · pagadores (solo usuarios registrados) · entradas de ledger (liquidación, reverso, perdón) · outbox/eventos.

## Observabilidad y operación

OpenTelemetry, logs estructurados con correlation ID, métricas de lag del outbox, lag por consumidor, profundidad de dead-letter, tasa de error de sync y de borradores marcados. Restauración programada con replay-equality sobre la copia.

## Entornos

Local (Docker Compose + LocalStack) · staging (espejo de producción) · producción. Todo definido en Terraform; migraciones corren en CI antes de cada release.
