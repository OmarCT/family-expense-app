# infra (Terraform, AWS)
Estructura prevista: `modules/` (network, ecs-service, rds, queue, bucket, secrets), `envs/staging`, `envs/prod`. Estado remoto en S3 con bloqueo. `terraform apply` solo desde CI con aprobación (ver ADR-0007). Pendiente: región y cuentas.
