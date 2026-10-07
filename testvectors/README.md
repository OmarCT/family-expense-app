# Vectores de prueba compartidos

Los mismos archivos JSON los ejecutan `services/core` (pytest, marcador `vectors`) y `packages/domain` (Vitest). Si los resultados difieren, el CI falla. Ver ADR-0002.

## Formato
```json
{ "schema_version": 1, "rule": "split_shares",
  "cases": [ { "id": "unico-dentro-del-archivo", "input": {}, "expected": {} } ] }
```
- Importes: enteros en centavos. Nada de decimales.
- Reglas previstas (Slice 1): `split_shares`, `allocate_extras`, `discounts_negative_items`, `group_expansion`, `unit_conversion`.
- Desempate de largest remainder (ADR-0002, ya fijado): `tiebreak_hash` (clave SHA-256 de `item_id`, `0x1F`, `user_id`), `tiebreak_order` y los empates de reparto en `split_shares_ties.json`. `item_id` es obligatorio cuando hay empate.
- Cada archivo declara su `rule`; el ejecutor busca el manejador por regla y omite explícitamente las que aún no existen.
- Añade el vector antes de tocar la regla. Un vector nunca se edita para "hacer pasar" una implementación: si cambia, es un cambio de regla y lleva ADR.
