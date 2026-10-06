# ADR-0004: Servidor como fuente de verdad; offline solo para altas

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
El teléfono encola escrituras con client ID y nunca fusiona. Offline permite **solo altas**; ediciones, borrados, cambios de grupo y liquidaciones requieren conexión. Las escrituras en cola que fallan validación de negocio se guardan como borradores marcados; solo se rechazan las malformadas o no autorizadas.

## Consecuencias
Sin CRDTs ni resolución de conflictos. Cursor viejo o hueco grande → re-bootstrap. Los payloads en cola llevan versión de API y se actualizan al llegar.
