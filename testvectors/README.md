# Vectores de prueba compartidos

Los mismos archivos JSON los ejecutan `services/core` (pytest, marcador `vectors`) y `packages/domain` (Vitest). Si los resultados difieren, el CI falla. Ver ADR-0002.

## Formato
```json
{ "schema_version": 1, "rule": "split_shares",
  "cases": [ { "id": "unico-dentro-del-archivo", "input": {}, "expected": {} } ] }
```
- Importes: enteros en centavos. Nada de decimales.
- Reglas previstas (Slice 1): `split_shares`, `allocate_extras`, `discounts_negative_items`, `group_expansion`, `unit_conversion`.
- Los casos de **empate** de largest remainder se añaden cuando se fije la función hash (ADR-0002); no los inventes antes.
- Añade el vector antes de tocar la regla. Un vector nunca se edita para "hacer pasar" una implementación: si cambia, es un cambio de regla y lleva ADR.
