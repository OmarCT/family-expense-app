# services/workers

Relay del outbox y consumidores (proyector de analítica, evaluador de presupuestos, notificador, limpieza de imágenes). Poetry: `poetry install`, `poetry run pytest`.

- Consumidores **idempotentes por event ID** y reconstruibles desde el log.
- Versión de evento desconocida → detenerse y alertar; nunca saltarla.
- Propagar el correlation ID de la solicitud original en logs y trazas.
- La cola se usa solo a través del adaptador (`queue/`), nunca `boto3` directo en la lógica.
- Antes de entregar o notificar, volver a comprobar visibilidad.
- Cambios aquí requieren prueba de fallos (duplicar, reordenar, retrasar, perder, matar entre "procesado" y "offset confirmado") y replay-equality.
