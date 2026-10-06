# infra (Terraform, AWS)

Región `us-east-2`. Estructura: `modules/` (hoy solo `ecr`; previstos network, ecs-service, rds, queue, bucket, secrets) y `envs/staging`, `envs/prod`. Estado remoto en S3 con bloqueo. `terraform apply` solo desde CI con aprobación (ver ADR-0007).

## Valores que no se versionan
El repo es público: el ID de la cuenta, el bucket de estado y cualquier credencial quedan fuera.

- `aws_account_id`: copia `envs/<env>/terraform.tfvars.example` a `terraform.tfvars` (ignorado por git) o pásalo como variable de CI. El proveedor usa `allowed_account_ids`, así que un `plan` contra otra cuenta falla.
- Backend: `terraform init -backend-config="bucket=..." -backend-config="key=<env>/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"`.

## Validar sin credenciales
`terraform init -backend=false && terraform validate` en cada entorno; CI lo corre en el job `terraform`.

## Pendiente
Bucket de estado (bootstrap manual), rol de CI con OIDC, y el resto de módulos.
