# ADR-0003: Ledger append-only y proyecciones reconstruibles

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
Gastos como revisiones inmutables; borrado = tombstone; liquidaciones, reversos y perdones = entradas. Cada escritura produce un evento. Toda proyección (balances de analítica, precios, presupuestos) se puede reconstruir desde el log; la prueba *replay-equality* lo verifica en CI.

## Alternativas descartadas
CRUD con auditoría aparte: no garantiza reconstrucción ni sincronización por secuencia.

## Consecuencias
Los eventos almacenados nunca se reescriben; los cambios de esquema usan upcasters. Las ediciones requieren revisión base (409 si está desactualizada).
