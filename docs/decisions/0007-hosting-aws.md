# ADR-0007: Hosting en AWS

- Estado: Aceptada
- Fecha: 2026-10-05

## Decisión
ECS Fargate para `core` y `workers`, RDS PostgreSQL con point-in-time recovery (core) y una segunda instancia para analítica, SNS + SQS FIFO detrás de un adaptador delgado, S3 privado con URLs firmadas, Secrets Manager, CloudWatch + OpenTelemetry. Región: **us-east-2 (Ohio)** para todos los entornos. **Dos cuentas AWS separadas**, una para staging y otra para producción (decisión del 2026-10-08, sustituye a la de una sola cuenta). Acceso por IAM Identity Center (SSO) con los perfiles `fea-staging` y `fea-prod`; cada cuenta guarda su estado en su propio bucket `fea-tfstate-<account_id>`. Los recursos conservan el prefijo del entorno (`fea-staging`, `fea-prod`). Los IDs de cuenta no se versionan (el repo es público): se pasan como variable `aws_account_id`. Infraestructura en Terraform (`infra/`). Local con Docker Compose + LocalStack.

## Alternativas descartadas
GCP y Azure: sin ventaja para este alcance. App Runner: menos control sobre workers de larga duración.

## Consecuencias
La cola se accede solo vía el adaptador para poder cambiarla. Staging espeja producción.
