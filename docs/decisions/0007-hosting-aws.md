# ADR-0007: Hosting en AWS

- Estado: Aceptada (estructura de cuentas pendiente)
- Fecha: 2026-10-05

## Decisión
ECS Fargate para `core` y `workers`, RDS PostgreSQL con point-in-time recovery (core) y una segunda instancia para analítica, SNS + SQS FIFO detrás de un adaptador delgado, S3 privado con URLs firmadas, Secrets Manager, CloudWatch + OpenTelemetry. Región: **us-east-2 (Ohio)** para todos los entornos. Infraestructura en Terraform (`infra/`). Local con Docker Compose + LocalStack.

## Alternativas descartadas
GCP y Azure: sin ventaja para este alcance. App Runner: menos control sobre workers de larga duración.

## Consecuencias
La cola se accede solo vía el adaptador para poder cambiarla. Staging espeja producción.
