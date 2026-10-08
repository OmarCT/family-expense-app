# Se aplica una sola vez por cuenta, a mano, con credenciales de administrador, usando el
# perfil de esa cuenta. El estado es local (no hay bucket antes de aplicarlo): usa un archivo
# de estado distinto por cuenta (-state) y guárdalos fuera del repo.
#
# environment = "staging": rol fea-ci-images, asumible desde la rama main, empuja a fea-staging/*.
# environment = "prod": rol fea-ci-promote, asumible solo desde el entorno "production" de GitHub;
#   empuja a fea-prod/* y lee fea-staging/* de la cuenta de staging (promoción de imágenes).
terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "aws_account_id" {
  type        = string
  description = "ID de la cuenta AWS. No se versiona."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "aws_account_id debe tener 12 dígitos."
  }
}

variable "environment" {
  type    = string
  default = "staging"

  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment debe ser staging o prod."
  }
}

# Solo para environment = "prod": cuenta de staging de la que se promueven las imágenes.
variable "staging_account_id" {
  type    = string
  default = ""
}

variable "aws_region" {
  type    = string
  default = "us-east-2"
}

variable "github_owner" {
  type    = string
  default = "OmarCT"
}

variable "github_repository" {
  type    = string
  default = "family-expense-app"
}

# GitHub incluye estos IDs en el claim `sub` del token OIDC; fijarlos evita que otro
# repositorio con el mismo nombre (o uno recreado) asuma el rol.
variable "github_owner_id" {
  type    = string
  default = "18475300"
}

variable "github_repository_id" {
  type    = string
  default = "1407649234"
}

locals {
  is_prod      = var.environment == "prod"
  github_repo  = "repo:${var.github_owner}@${var.github_owner_id}/${var.github_repository}@${var.github_repository_id}"
  oidc_subject = local.is_prod ? "${local.github_repo}:environment:production" : "${local.github_repo}:ref:refs/heads/main"
  role_name    = local.is_prod ? "fea-ci-promote" : "fea-ci-images"
  policy_name  = local.is_prod ? "promote-images" : "push-staging-images"
}

provider "aws" {
  region              = var.aws_region
  allowed_account_ids = [var.aws_account_id]

  default_tags {
    tags = {
      project    = "family-expense-app"
      managed_by = "terraform"
      stack      = "bootstrap"
    }
  }
}

resource "aws_s3_bucket" "tfstate" {
  bucket = "fea-tfstate-${var.aws_account_id}"
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "ci_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [local.oidc_subject]
    }
  }
}

resource "aws_iam_role" "ci_images" {
  name               = local.role_name
  assume_role_policy = data.aws_iam_policy_document.ci_assume.json

  lifecycle {
    precondition {
      condition     = !local.is_prod || can(regex("^[0-9]{12}$", var.staging_account_id))
      error_message = "Con environment = prod hace falta staging_account_id (12 dígitos)."
    }
  }
}

data "aws_iam_policy_document" "ci_images" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = ["arn:aws:ecr:${var.aws_region}:${var.aws_account_id}:repository/fea-${var.environment}/*"]
  }

  dynamic "statement" {
    for_each = local.is_prod ? [1] : []

    content {
      actions = [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
      ]
      resources = ["arn:aws:ecr:${var.aws_region}:${var.staging_account_id}:repository/fea-staging/*"]
    }
  }
}

resource "aws_iam_role_policy" "ci_images" {
  name   = local.policy_name
  role   = aws_iam_role.ci_images.id
  policy = data.aws_iam_policy_document.ci_images.json
}

output "tfstate_bucket" {
  value = aws_s3_bucket.tfstate.bucket
}

output "ci_role_arn" {
  value = aws_iam_role.ci_images.arn
}

# Alias del anterior: en staging es el rol de publicación; en prod, el de promoción.
output "ci_images_role_arn" {
  value = aws_iam_role.ci_images.arn
}
