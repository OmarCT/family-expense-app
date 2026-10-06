# ADR-0006: Outbox transaccional y feed por secuencia

- Estado: Aceptada (mecanismo de secuencia por definir en Slice 2)
- Fecha: 2026-10-05

## Contexto
Una secuencia asignada al insertar puede confirmarse fuera de orden y hacer que un cliente se salte cambios.

## Decisión
El evento se inserta en la misma transacción que la escritura. La secuencia por hogar se asigna **al confirmar**, en orden (propuesta: contador por hogar bloqueado en la transacción, o relay único que numera leyendo en orden de commit). El relay publica a SNS→SQS FIFO con `MessageGroupId = household_id`. Los consumidores son idempotentes por event ID.

## Consecuencias
Se valida con fault injection (duplicar, reordenar, retrasar, perder, matar consumidor entre "procesado" y "offset confirmado"). El push es solo una pista: el cliente siempre consulta el feed.
