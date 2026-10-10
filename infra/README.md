# infra (Terraform, AWS)

Región `us-east-2`. Estructura: `modules/` (hoy `ecr`, `network` y `rds`; previstos ecs-service, queue, bucket, secrets) y `envs/staging`, `envs/prod`. Estado remoto en S3 con bloqueo. `terraform apply` solo desde CI con aprobación (ver ADR-0007).

## Cuentas
Staging y producción viven en cuentas AWS distintas (ADR-0007), con acceso SSO. Usa siempre el perfil del entorno: `export AWS_PROFILE=fea-staging` o `fea-prod` (inicia sesión con `aws sso login --profile ...`). El proveedor usa `allowed_account_ids`, así que aplicar `envs/prod` con el perfil de staging falla en lugar de crear recursos en la cuenta equivocada.

## Valores que no se versionan
El repo es público: el ID de la cuenta, el bucket de estado y cualquier credencial quedan fuera.

- `aws_account_id`: el de la cuenta de ese entorno (no el de la otra). Copia `envs/<env>/terraform.tfvars.example` a `terraform.tfvars` (ignorado por git) o pásalo como variable de CI. El proveedor usa `allowed_account_ids`, así que un `plan` contra otra cuenta falla.
- Backend: `terraform init -backend-config="bucket=..." -backend-config="key=<env>/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"`.

## Red y base de datos de staging
`modules/network` y `modules/rds` (ver ADR-0012), conectados en `envs/staging`. El `plan` real contra la cuenta de staging da **24 a crear, 0 cambios, 0 destrucciones**. Coste fijo aproximado: **unos 14 USD al mes** (instancia `db.t4g.micro` a 0,016 USD/h más 20 GB de gp3 a 0,115 USD/GB-mes, según la API de precios de AWS en `us-east-2`); no hay NAT.

```bash
cd infra/envs/staging && export AWS_PROFILE=fea-staging
terraform plan    # Plan: 24 to add, 0 to change, 0 to destroy
terraform apply   # la base tarda unos 10 minutos
terraform output core_database   # endpoint, puerto, nombre y ARN del secreto del administrador
```

La base es privada: no hay forma de conectar desde fuera de la VPC (tampoco desde tu equipo) hasta que existan las tareas de ECS. La contraseña del administrador está solo en el secreto de Secrets Manager.

Análisis estático (`trivy config`): quedan avisos que se aceptan a propósito en staging: salida TCP 443 a `0.0.0.0/0` (Auth0 y las APIs de AWS no tienen IP fija), protección contra borrado desactivada, autenticación IAM de la base no usada, cifrado con claves administradas por AWS en lugar de CMK, y sin registros de flujo de la VPC. Revisar antes de producción.

## Validar sin credenciales
`terraform init -backend=false && terraform validate` en cada entorno; CI lo corre en el job `terraform`.

## Bootstrap (una sola vez, a mano)
`infra/bootstrap` crea el bucket de estado (versionado, cifrado, sin acceso público), el proveedor OIDC de GitHub y un rol de CI. En staging (el valor por defecto) es `fea-ci-images`: solo puede subir imágenes a `fea-staging/*` y solo desde la rama `main`. En producción (`environment = "prod"`) es `fea-ci-promote`; ver la sección siguiente.

1. `cd infra/bootstrap && cp terraform.tfvars.example staging.tfvars` y escribe el ID de la cuenta de staging. Cada entorno usa su propio archivo (`staging.tfvars`, `prod.tfvars`); no uses `terraform.tfvars`.
2. Con el perfil SSO de la cuenta: `./run.sh staging init && ./run.sh staging apply`. Su estado es local; guárdalo fuera del repo.
3. En GitHub, Settings → Secrets and variables → Actions → Variables: `AWS_ROLE_ARN` con el output `ci_images_role_arn` (y `AWS_REGION` si no es `us-east-2`). Mientras `AWS_ROLE_ARN` no exista, el job `images` solo construye la imagen y no publica.
4. Para cada entorno: `terraform init -backend-config="bucket=<tfstate_bucket>" -backend-config="key=<env>/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"` (requiere Terraform 1.10 o superior) y `terraform apply` para crear los repositorios ECR.

## Producción: ECR propio y promoción con aprobación
Producción no recibe nada de un merge. Staging publica `fea-staging/core:<sha>` desde `main`; para llegar a producción, alguien lanza a mano el workflow `promote` con ese SHA. El job usa el entorno `production` de GitHub (exige aprobación), comprueba que el commit está en `main` y que su CI terminó en `success`, y copia la imagen a `fea-prod/core:<sha>` con el rol `fea-ci-promote`. Ese rol solo lo puede asumir el entorno `production`, y las etiquetas son inmutables.

Orden de puesta en marcha (todo a mano, con el perfil SSO de cada cuenta; los `.tfvars` y los estados están ignorados por git):

1. **Bootstrap de producción** (`fea-prod`). Usa siempre `./run.sh`: fija juntos el perfil, el archivo de variables y el archivo de estado de un solo entorno y se niega si no cuadran. No ejecutes `terraform` a mano aquí: con credenciales de una cuenta y el estado de otra, Terraform puede dar por borrados los recursos de la otra cuenta y sobrescribir su estado.
   ```bash
   cd infra/bootstrap
   printf 'aws_account_id     = "<id de prod>"\nenvironment        = "prod"\nstaging_account_id = "<id de staging>"\n' > prod.tfvars
   ./run.sh prod init
   ./run.sh prod plan
   ./run.sh prod apply
   ```
   El estado de producción queda en `terraform.prod.tfstate` (el de staging es `terraform.tfstate`); ambos están ignorados por git, haz copia de los dos.
   El bootstrap crea el bucket de estado **en `us-east-2`**. Antes de aplicar, comprueba que no exista ya uno con ese nombre creado a mano: `aws s3api get-bucket-location --bucket fea-tfstate-<id de prod>` (`None` significa `us-east-1`). La CLI crea los buckets en la región del perfil, y los perfiles SSO de este proyecto tienen `us-east-1` por defecto.
   - Si no existe, el `apply` de arriba lo crea.
   - Si existe en `us-east-1` y está vacío, bórralo y aplica: `aws s3api delete-bucket --bucket fea-tfstate-<id de prod> --region us-east-1 --profile fea-prod`. Un bucket de otra región no se puede importar ni reutilizar con `region = "us-east-2"`.
   - Si existe en `us-east-2`, impórtalo antes del `plan`: `for r in aws_s3_bucket.tfstate aws_s3_bucket_versioning.tfstate aws_s3_bucket_server_side_encryption_configuration.tfstate aws_s3_bucket_public_access_block.tfstate; do ./run.sh prod import "$r" fea-tfstate-<id de prod>; done`.

   Anota el output `ci_role_arn`. Conviene fijar la región de los perfiles: `aws configure set region us-east-2 --profile fea-prod` (y lo mismo con `fea-staging`).
2. **Staging: permitir la lectura de producción.** En `envs/staging/terraform.tfvars` añade `prod_account_id = "<id de prod>"` y aplica con `AWS_PROFILE=fea-staging` (crea las políticas de repositorio).
3. **Producción: repositorios.** En `envs/prod` copia `terraform.tfvars.example`, pon el ID de prod, `terraform init -backend-config="bucket=fea-tfstate-<id de prod>" -backend-config="key=prod/terraform.tfstate" -backend-config="region=us-east-2" -backend-config="use_lockfile=true"` y `terraform apply` con `AWS_PROFILE=fea-prod`.
4. **GitHub.** Settings → Environments → `production`: *Required reviewers* (tú) y *Deployment branches* limitado a `main` (sin esto, otra rama podría lanzar una versión modificada del workflow). En las variables del entorno: `PROD_ROLE_ARN` (el `ci_role_arn` del paso 1), `PROD_ACCOUNT_ID` y `STAGING_ACCOUNT_ID`.
5. **Promover.** Actions → `promote` → Run workflow con el SHA de una imagen que exista en `fea-staging/core`.

Si el paso 5 falla con `Not authorized to perform sts:AssumeRoleWithWebIdentity`, consulta CloudTrail (`AssumeRoleWithWebIdentity`) en la cuenta de producción: el `sub` real del token con entorno debe coincidir con el de la política de confianza.

## Pendiente
Rol de CI para `plan`/`apply` de los entornos, imagen de `workers` (cuando tenga un proceso que ejecutar) y el resto de módulos.
