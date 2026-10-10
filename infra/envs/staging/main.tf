terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Configuración parcial: bucket y tabla de bloqueo se pasan con
  # `terraform init -backend-config=...` y no se versionan.
  backend "s3" {}
}

variable "aws_account_id" {
  type        = string
  description = "ID de la cuenta AWS. No se versiona: va en un .tfvars local o en una variable de CI."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "aws_account_id debe tener 12 dígitos."
  }
}

variable "prod_account_id" {
  type        = string
  default     = ""
  description = "Cuenta de producción autorizada a leer las imágenes para promoverlas. Vacío: nadie."

  validation {
    condition     = var.prod_account_id == "" || can(regex("^[0-9]{12}$", var.prod_account_id))
    error_message = "prod_account_id debe estar vacío o tener 12 dígitos."
  }
}

variable "aws_region" {
  type    = string
  default = "us-east-2"
}

provider "aws" {
  region              = var.aws_region
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = {
      project     = "family-expense-app"
      environment = "staging"
      managed_by  = "terraform"
    }
  }
}

module "ecr" {
  source       = "../../modules/ecr"
  name_prefix  = "fea-staging"
  repositories = ["core", "workers"]

  pull_account_ids = var.prod_account_id == "" ? [] : [var.prod_account_id]
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

module "network" {
  source   = "../../modules/network"
  name     = "fea-staging"
  vpc_cidr = "10.10.0.0/16"
  nat_mode = "none"
}

module "rds_core" {
  source = "../../modules/rds"
  name   = "fea-staging-core"

  vpc_id                    = module.network.vpc_id
  subnet_ids                = module.network.private_subnet_ids
  client_security_group_ids = [module.network.app_security_group_id]

  deletion_protection = false
}

output "network" {
  value = {
    vpc_id             = module.network.vpc_id
    private_subnet_ids = module.network.private_subnet_ids
    public_subnet_ids  = module.network.public_subnet_ids
  }
}

output "core_database" {
  value = {
    endpoint          = module.rds_core.endpoint
    port              = module.rds_core.port
    database_name     = module.rds_core.database_name
    master_secret_arn = module.rds_core.master_secret_arn
  }
}
