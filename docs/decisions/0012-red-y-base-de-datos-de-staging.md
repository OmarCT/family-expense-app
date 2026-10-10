# ADR-0012: Red y base de datos core en staging

- Estado: Aceptada
- Fecha: 2026-10-10

## Contexto
`core` necesita PostgreSQL con recuperación a un instante (ADR-0007) y las tareas de ECS necesitarán red. Staging debe poder desmontarse y no acumular coste fijo mientras no haya tareas.

## Decisión
- **VPC por entorno con CIDR disjunto**: staging `10.10.0.0/16`, producción `10.20.0.0/16` (reservado), por si hay que conectarlas. Dos zonas, subredes públicas y privadas, el grupo de seguridad por defecto sin reglas y un endpoint de pasarela a S3 (gratuito) para las capas de ECR.
- **Sin NAT por ahora** (`nat_mode = "none"`): las subredes privadas no salen a internet. Se activa `single` o `per_az` cuando existan tareas que necesiten llegar a Auth0 o a las APIs de AWS.
- **Grupo de seguridad de la aplicación** sin entradas y con salida solo a TCP 443 (Auth0, AWS) y a PostgreSQL dentro de la VPC. La base de datos solo acepta el puerto 5432 desde ese grupo, por referencia, no por IP.
- **RDS PostgreSQL 16** privada: `db.t4g.micro`, gp3 cifrado con autoescalado, `rds.force_ssl=1`, copias con 7 días de retención (PITR), Performance Insights de 7 días y registros a CloudWatch. La contraseña del administrador la genera RDS y vive en Secrets Manager (`manage_master_user_password`): nunca pasa por Terraform ni por su estado.
- Staging sin protección contra borrado (con instantánea final); el módulo la activa por defecto para producción.

## Alternativas descartadas
- NAT desde el principio: unos 32 USD al mes sin tareas que lo usen.
- Tareas en subredes públicas para evitar el NAT: ya no refleja producción.
- Segunda instancia (analítica) ahora: pertenece al Slice 2.
- Claves propias (CMK) y registros de flujo de la VPC: coste y complejidad sin beneficio hoy; se reevalúan antes de producción real.

## Consecuencias
Coste fijo aproximado de staging: unos 14 USD al mes (instancia 0,016 USD/h y 20 GB a 0,115 USD/GB-mes, precios de la API de AWS en `us-east-2`), más almacenamiento de copias por encima del tamaño de la base y registros. Al añadir ECS habrá que decidir NAT frente a endpoints de interfaz. Nadie puede conectar a la base desde fuera de la VPC; las migraciones correrán como tarea de ECS. El usuario de la aplicación (sin `BYPASSRLS` y sin ser dueño de las tablas) se crea en una migración del Slice 1; el administrador de RDS no se usa para servir tráfico.
