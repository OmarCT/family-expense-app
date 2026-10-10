variable "name" {
  type        = string
  description = "Identificador de la instancia, p. ej. fea-staging-core"
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subredes privadas (al menos dos zonas)"
}

variable "client_security_group_ids" {
  type        = list(string)
  description = "Grupos de seguridad autorizados a conectar al puerto 5432"
}

variable "database_name" {
  type    = string
  default = "core"
}

variable "master_username" {
  type    = string
  default = "fea_admin"
}

variable "engine_version" {
  type        = string
  default     = "16"
  description = "Versión mayor; RDS elige la menor y la actualiza sola"
}

variable "instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "max_allocated_storage" {
  type        = number
  default     = 100
  description = "Tope del autoescalado de almacenamiento (GiB)"
}

variable "multi_az" {
  type    = bool
  default = false
}

# Con backup_retention_period >= 1 RDS conserva los registros de transacciones y permite
# restaurar a un instante concreto (PITR, ADR-0007).
variable "backup_retention_days" {
  type    = number
  default = 7

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 35
    error_message = "backup_retention_days debe estar entre 1 y 35 para tener PITR."
  }
}

variable "deletion_protection" {
  type    = bool
  default = true
}

resource "aws_db_subnet_group" "this" {
  name       = var.name
  subnet_ids = var.subnet_ids

  tags = { Name = var.name }
}

resource "aws_security_group" "db" {
  name        = "${var.name}-db"
  description = "Acceso a PostgreSQL ${var.name}"
  vpc_id      = var.vpc_id

  tags = { Name = "${var.name}-db" }
}

resource "aws_vpc_security_group_ingress_rule" "from_clients" {
  for_each = { for i, id in var.client_security_group_ids : tostring(i) => id }

  security_group_id            = aws_security_group.db.id
  referenced_security_group_id = each.value
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  description                  = "PostgreSQL desde las tareas de la aplicacion"
}

resource "aws_db_parameter_group" "this" {
  name   = var.name
  family = "postgres16"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  tags = { Name = var.name }
}

resource "aws_db_instance" "this" {
  identifier     = var.name
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  db_name  = var.database_name
  username = var.master_username

  # RDS genera la contraseña y la guarda en Secrets Manager: nunca pasa por Terraform ni por su estado.
  manage_master_user_password = true

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  parameter_group_name   = aws_db_parameter_group.this.name
  publicly_accessible    = false
  multi_az               = var.multi_az

  backup_retention_period = var.backup_retention_days
  backup_window           = "08:00-09:00"
  maintenance_window      = "sun:09:30-sun:10:30"
  copy_tags_to_snapshot   = true

  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.name}-final"

  auto_minor_version_upgrade            = true
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  tags = { Name = var.name }
}

output "endpoint" {
  value = aws_db_instance.this.address
}

output "port" {
  value = aws_db_instance.this.port
}

output "database_name" {
  value = aws_db_instance.this.db_name
}

output "master_secret_arn" {
  description = "Secreto con las credenciales del usuario administrador"
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}

output "security_group_id" {
  value = aws_security_group.db.id
}
