# ADR-0002: Dinero exacto en centavos con vectores compartidos

- Estado: Aceptada (detalle del desempate pendiente)
- Fecha: 2026-10-05

## Contexto
El servidor (Python) y los clientes (TypeScript) calculan splits. Cualquier divergencia de un centavo rompe los balances.

## Decisión
- Importes como enteros en centavos con código de moneda (ya en cada monto).
- Reparto por *largest remainder*; empate resuelto con un hash determinista. **Pendiente fijar la función hash** (propuesta: SHA-256 de `item_id || user_id`, orden ascendente).
- Extras (propina, impuestos, descuentos) se asignan proporcionalmente con la misma regla.
- Un único conjunto de casos JSON en `testvectors/` que ejecutan ambas suites; el CI falla si discrepan.
- Prohibido `float` en dominio, API y base de datos.

## Alternativas descartadas
Decimal en el servidor y número en el cliente (redondeos distintos); generar el código de un solo lado (acopla runtimes).

## Consecuencias
Todo cambio de regla empieza por un vector. Los vectores son parte del contrato público interno.
