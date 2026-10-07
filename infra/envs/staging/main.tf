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
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}
