# infra (Terraform, AWS)

Región `us-east-2`. Estructura: `modules/` (hoy solo `ecr`; previstos network, ecs-service, rds, queue, bucket, secrets) y `envs/staging`, `envs/prod`. Estado remoto en S3 con bloqueo. `terraform apply` solo desde CI con aprobación (ver ADR-0007).

## Cuentas
Staging y producción viven en cuentas AWS distintas (ADR-0007), con acceso SSO. Usa siempre el perfil del entorno: `export AWS_PROFILE=fea-staging` o `fea-prod` (inicia sesión con `aws sso login --profile ...`). El proveedor usa `allowed_account_ids`, así que aplicar `envs/prod` con el perfil de staging falla en lugar de crear recursos en la cuenta equivocada.

## Valores que no se versionan
El repo es público: el ID de la cuenta, el bucket de estado y cualquier credencial quedan fuera.

- `aws_account_id`: el de la cuenta de ese entorno (no el de la otra). Copia `envs/<env>/terraform.tfvars.example` a `terraform.tfvars` (ignorado por git) o pásalo como variable de CI. El proveedor usa `allowed_account_ids`, así que un `plan` contra otra cuenta falla.
- Backend: `terraform init -backend-config="bucket=..." -backend-config="key=<env>/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"`.

## Validar sin credenciales
`terraform init -backend=false && terraform validate` en cada entorno; CI lo corre en el job `terraform`.

## Bootstrap (una sola vez, a mano)
`infra/bootstrap` crea el bucket de estado (versionado, cifrado, sin acceso público), el proveedor OIDC de GitHub y el rol `fea-ci-images`, que solo puede subir imágenes a `fea-staging/*` y solo desde la rama `main`.

1. `cd infra/bootstrap && cp terraform.tfvars.example terraform.tfvars` y escribe el ID de cuenta.
2. Con credenciales de administrador: `terraform init && terraform apply`. Su estado es local; guárdalo fuera del repo.
3. En GitHub, Settings → Secrets and variables → Actions → Variables: `AWS_ROLE_ARN` con el output `ci_images_role_arn` (y `AWS_REGION` si no es `us-east-2`). Mientras `AWS_ROLE_ARN` no exista, el job `images` solo construye la imagen y no publica.
4. Para cada entorno: `terraform init -backend-config="bucket=<tfstate_bucket>" -backend-config="key=<env>/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"` (requiere Terraform 1.10 o superior) y `terraform apply` para crear los repositorios ECR.

## Producción
La cuenta de producción tiene hoy solo el bucket de estado. El bootstrap de arriba está escrito para staging (el rol de CI solo alcanza `fea-staging/*`) y no se ha decidido cómo llegan las imágenes a producción: publicar en un ECR propio de la cuenta de producción mediante una promoción con aprobación (rol distinto, con `sub` de entorno), o permitir que esa cuenta lea el ECR de staging. No apliques el bootstrap en producción tal cual hasta decidirlo.

## Pendiente
Rol de CI para `plan`/`apply` de los entornos, imagen de `workers` (cuando tenga un proceso que ejecutar) y el resto de módulos.
