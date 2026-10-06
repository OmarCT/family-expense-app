# ADR-0007: Hosting en AWS

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
ECS Fargate para `core` y `workers`, RDS PostgreSQL con point-in-time recovery (core) y una segunda instancia para analítica, SNS + SQS FIFO detrás de un adaptador delgado, S3 privado con URLs firmadas, Secrets Manager, CloudWatch + OpenTelemetry. Región: **us-east-2 (Ohio)** para todos los entornos. Por ahora una sola cuenta AWS aloja staging y producción, separados por prefijo de nombre (`fea-staging`, `fea-prod`); se reevalúa separar cuentas antes de usar datos reales. El ID de la cuenta no se versiona (el repo es público): se pasa como variable `aws_account_id`. Infraestructura en Terraform (`infra/`). Local con Docker Compose + LocalStack.

## Alternativas descartadas
GCP y Azure: sin ventaja para este alcance. App Runner: menos control sobre workers de larga duración.

## Consecuencias
La cola se accede solo vía el adaptador para poder cambiarla. Staging espeja producción.
