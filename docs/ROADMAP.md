# Roadmap

Marca cada punto solo cuando sus pruebas pasan en CI. Plan detallado: `docs/specs/implementation-plan.md`.

## Slice 0 — Foundations (S) ← activo
- [x] Monorepo, pnpm workspaces, Poetry en `services/core` y `services/workers`
- [x] CI: lint, tipos, tests en ambos lenguajes, contrato, vectores compartidos, imágenes en merge
- [ ] Entornos local / staging / prod en Terraform
- [ ] Auth0: tenant dev y prod (email code, Google, Apple)
- [x] OpenAPI `/v1`: error único, client ID, revisión base; cliente TS generado
- [x] i18n con claves, `es-MX`
- [x] Alembic + sobre de evento con `schema_version`
- [ ] Observabilidad base (logs estructurados, OTel, sin PII)
- **Salida:** usuario firmado llama `/v1` desde ambos shells; deploy a staging por CI; un vector incorrecto rompe el build

## Slice 1 — Money correctness (L)
- [ ] Vectores de prueba primero (splits, largest remainder, extras, descuentos, grupos, unidades)
- [ ] Reglas en `packages/domain` y `services/core` pasando el mismo archivo
- [ ] Modelo de datos
- [ ] RLS + suite de frontera
- [ ] API de escritura (crear, editar con revisión base → 409, tombstone, liquidar, reversar, perdonar)
- [ ] Balances y "liquidar con menos pagos"
- [ ] Clientes online
- [ ] Tests property-based de invariantes
- **Salida:** dos semanas de uso real, balances cuadran, suites verdes

## Slice 2 — Distributed spine (M)
- [ ] Outbox en la transacción · [ ] Relay a SQS · [ ] Feed de cambios · [ ] Push hints
- [ ] Primer proyector · [ ] Pantalla de analítica web · [ ] Fault injection + replay-equality · [ ] Métricas y alertas

## Slice 3 — Offline-first (L)
- [ ] SQLite local · [ ] IDs de cliente · [ ] sync-client · [ ] Bootstrap · [ ] Regla de caducidad
- [ ] Validación de escrituras en cola (borradores marcados) · [ ] Versionado de payload · [ ] Purga al remover · [ ] Tests de red inestable

## Slice 4 — Drafts, scanning, catalog, price history (L)
- [ ] Estado borrador · [ ] Catálogo de productos · [ ] Unidades e historial de precios · [ ] Escáner on-device
- [ ] Imágenes (bucket privado, URLs firmadas) · [ ] Pantalla de confirmación · [ ] Proyector de precios · [ ] Manejo participants-only

## Slice 5 — Budgets, alerts, recurring, lifecycle (L)
- [ ] Presupuestos · [ ] Evaluador de alertas · [ ] Bandeja de notificaciones · [ ] Reglas recurrentes
- [ ] Alertas de precio · [ ] Exportación · [ ] Salir/borrar cuenta · [ ] Seguridad · [ ] Release (tiendas, privacidad, restore drill)

## Pendientes de decisión
- [ ] Horas semanales disponibles (para convertir tallas S/M/L en fechas)
- [ ] Función hash exacta del desempate de largest remainder (ADR-0002)
- [x] Región AWS: us-east-2 (ADR-0007)
- [x] Cuenta de AWS: una sola para staging y prod por ahora (ADR-0007)
