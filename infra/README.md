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
`infra/bootstrap` crea el bucket de estado (versionado, cifrado, sin acceso público), el proveedor OIDC de GitHub y un rol de CI. En staging (el valor por defecto) es `fea-ci-images`: solo puede subir imágenes a `fea-staging/*` y solo desde la rama `main`. En producción (`environment = "prod"`) es `fea-ci-promote`; ver la sección siguiente.

1. `cd infra/bootstrap && cp terraform.tfvars.example terraform.tfvars` y escribe el ID de cuenta.
2. Con credenciales de administrador: `terraform init && terraform apply`. Su estado es local; guárdalo fuera del repo.
3. En GitHub, Settings → Secrets and variables → Actions → Variables: `AWS_ROLE_ARN` con el output `ci_images_role_arn` (y `AWS_REGION` si no es `us-east-2`). Mientras `AWS_ROLE_ARN` no exista, el job `images` solo construye la imagen y no publica.
4. Para cada entorno: `terraform init -backend-config="bucket=<tfstate_bucket>" -backend-config="key=<env>/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"` (requiere Terraform 1.10 o superior) y `terraform apply` para crear los repositorios ECR.

## Producción: ECR propio y promoción con aprobación
Producción no recibe nada de un merge. Staging publica `fea-staging/core:<sha>` desde `main`; para llegar a producción, alguien lanza a mano el workflow `promote` con ese SHA. El job usa el entorno `production` de GitHub (exige aprobación), comprueba que el commit está en `main` y que su CI terminó en `success`, y copia la imagen a `fea-prod/core:<sha>` con el rol `fea-ci-promote`. Ese rol solo lo puede asumir el entorno `production`, y las etiquetas son inmutables.

Orden de puesta en marcha (todo a mano, con el perfil SSO de cada cuenta; los `.tfvars` y los estados están ignorados por git):

1. **Bootstrap de producción** (`fea-prod`). Usa un archivo de estado propio: el predeterminado es el de staging.
   ```bash
   export AWS_PROFILE=fea-prod AWS_REGION=us-east-2
   cd infra/bootstrap
   printf 'aws_account_id     = "<id de prod>"\nenvironment        = "prod"\nstaging_account_id = "<id de staging>"\n' > prod.tfvars
   terraform init
   for r in aws_s3_bucket.tfstate aws_s3_bucket_versioning.tfstate \
            aws_s3_bucket_server_side_encryption_configuration.tfstate \
            aws_s3_bucket_public_access_block.tfstate; do
     terraform import -state=terraform.prod.tfstate -var-file=prod.tfvars "$r" fea-tfstate-<id de prod>
   done
   terraform plan  -state=terraform.prod.tfstate -var-file=prod.tfvars
   terraform apply -state=terraform.prod.tfstate -var-file=prod.tfvars
   ```
   El bucket ya existe, por eso se importa. Anota el output `ci_role_arn`.
2. **Staging: permitir la lectura de producción.** En `envs/staging/terraform.tfvars` añade `prod_account_id = "<id de prod>"` y aplica con `AWS_PROFILE=fea-staging` (crea las políticas de repositorio).
3. **Producción: repositorios.** En `envs/prod` copia `terraform.tfvars.example`, pon el ID de prod, `terraform init -backend-config="bucket=fea-tfstate-<id de prod>" -backend-config="key=prod/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"` y `terraform apply` con `AWS_PROFILE=fea-prod`.
4. **GitHub.** Settings → Environments → `production`: *Required reviewers* (tú) y *Deployment branches* limitado a `main` (sin esto, otra rama podría lanzar una versión modificada del workflow). En las variables del entorno: `PROD_ROLE_ARN` (el `ci_role_arn` del paso 1), `PROD_ACCOUNT_ID` y `STAGING_ACCOUNT_ID`.
5. **Promover.** Actions → `promote` → Run workflow con el SHA de una imagen que exista en `fea-staging/core`.

Si el paso 5 falla con `Not authorized to perform sts:AssumeRoleWithWebIdentity`, consulta CloudTrail (`AssumeRoleWithWebIdentity`) en la cuenta de producción: el `sub` real del token con entorno debe coincidir con el de la política de confianza.

## Pendiente
Rol de CI para `plan`/`apply` de los entornos, imagen de `workers` (cuando tenga un proceso que ejecutar) y el resto de módulos.
