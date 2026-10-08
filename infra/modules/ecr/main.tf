variable "name_prefix" {
  type        = string
  description = "Prefijo de los repositorios, p. ej. fea-staging"
}

variable "repositories" {
  type        = set(string)
  description = "Nombres de repositorio sin prefijo"
}

variable "keep_images" {
  type    = number
  default = 20
}

variable "pull_account_ids" {
  type        = list(string)
  default     = []
  description = "Cuentas que pueden leer estas imágenes (promoción a otra cuenta)"
}

resource "aws_ecr_repository" "this" {
  for_each             = var.repositories
  name                 = "${var.name_prefix}/${each.key}"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

data "aws_iam_policy_document" "pull" {
  count = length(var.pull_account_ids) > 0 ? 1 : 0

  statement {
    sid    = "CrossAccountPull"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [for id in var.pull_account_ids : "arn:aws:iam::${id}:root"]
    }

    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
  }
}

resource "aws_ecr_repository_policy" "pull" {
  for_each   = { for k, r in aws_ecr_repository.this : k => r if length(var.pull_account_ids) > 0 }
  repository = each.value.name
  policy     = data.aws_iam_policy_document.pull[0].json
}

resource "aws_ecr_lifecycle_policy" "this" {
  for_each   = aws_ecr_repository.this
  repository = each.value.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Conservar las ultimas ${var.keep_images} imagenes"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = var.keep_images
      }
      action = { type = "expire" }
    }]
  })
}

output "repository_urls" {
  value = { for k, r in aws_ecr_repository.this : k => r.repository_url }
}
