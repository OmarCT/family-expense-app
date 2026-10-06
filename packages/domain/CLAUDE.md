# packages/domain

Reglas de dinero y unidades en TypeScript. Espejo exacto de `services/core/src/fea_core/money`.
- Solo enteros (centavos); sin `number` fraccionario ni librerías de punto flotante.
- Scripts: `test` y `test:vectors` (Vitest sobre `testvectors/*.json`).
- No agregues una regla sin su vector en `testvectors/`; ambos lenguajes deben pasar.
