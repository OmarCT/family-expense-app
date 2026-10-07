# ADR-0002: Dinero exacto en centavos con vectores compartidos

- Estado: Aceptada
- Fecha: 2026-10-05

## Contexto
El servidor (Python) y los clientes (TypeScript) calculan splits. Cualquier divergencia de un centavo rompe los balances.

## Decisión
- Importes como enteros en centavos con código de moneda (ya en cada monto).
- Reparto por *largest remainder*. El residuo de cada participante es entero y exacto (`total * peso mod suma_de_pesos`); no hay fracciones.
- **Desempate (fijado 2026-10-07):** entre participantes con el mismo residuo, recibe antes el centavo sobrante quien tenga la **menor clave**, comparada byte a byte sin signo. La clave es `SHA-256(utf8(item_id) || 0x1F || utf8(user_id))`.
  - El separador `0x1F` es obligatorio: sin él, `("ab","c")` y `("a","bc")` darían la misma clave.
  - La clave depende del ítem: el mismo participante no gana siempre los centavos sobrantes.
  - Los `user_id` de un reparto son únicos; con duplicados la regla falla en lugar de elegir.
  - `item_id` es obligatorio cuando hay empate.
- SHA-256 en Python con `hashlib`. En TypeScript con una implementación propia sin dependencias (Hermes no incluye `crypto`), validada con los vectores NIST y contra `node:crypto`.
- Extras (propina, impuestos, descuentos) se asignan proporcionalmente con la misma regla.
- Un único conjunto de casos JSON en `testvectors/` que ejecutan ambas suites; el CI falla si discrepan.
- Prohibido `float` en dominio, API y base de datos.

## Alternativas descartadas
Decimal en el servidor y número en el cliente (redondeos distintos); generar el código de un solo lado (acopla runtimes).

## Consecuencias
Los vectores `tiebreak_hash`, `tiebreak_order` y `split_shares_ties` fijan la regla; los dos primeros ya se ejecutan en ambos lenguajes. Los casos de `split_shares_ties` los generó un script de referencia y están pendientes de que la implementación del Slice 1, escrita desde este ADR, los reproduzca de forma independiente.
Todo cambio de regla empieza por un vector. Los vectores son parte del contrato público interno.
