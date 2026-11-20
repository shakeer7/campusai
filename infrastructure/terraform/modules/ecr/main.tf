variable "environment" { type = string }

locals {
  repositories = ["campusai-backend", "campusai-frontend", "campusai-mcp"]
}

resource "aws_ecr_repository" "repos" {
  for_each             = toset(local.repositories)
  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = each.value
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Free Tier Lifecycle policy: keep only the latest 5 versioned images to stay within 500MB Free Tier / low storage
resource "aws_ecr_lifecycle_policy" "repo_policy" {
  for_each   = aws_ecr_repository.repos
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only last 5 images to optimize storage costs"
      selection = {
        tagStatus   = "any"
        countType   = "sinceImagePushed"
        countUnit   = "days"
        countNumber = 14
      }
      action = {
        type = "expire"
      }
    }]
  })
}

output "repository_urls" {
  value = { for k, v in aws_ecr_repository.repos : k => v.repository_url }
}
