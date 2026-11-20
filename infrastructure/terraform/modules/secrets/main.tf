variable "environment" { type = string }
variable "db_name" { type = string }
variable "db_username" { type = string }

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "campusai-${var.environment}-app-secrets"
  description = "Managed secrets for CampusAI database, JWT, and MCP API keys"
}

resource "aws_secretsmanager_secret_version" "app_secrets_val" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    POSTGRES_USER     = var.db_username
    POSTGRES_PASSWORD = random_password.db_password.result
    POSTGRES_DB       = var.db_name
    JWT_SECRET_KEY    = random_password.jwt_secret.result
  })
}

output "db_master_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "secret_arn" {
  value = aws_secretsmanager_secret.app_secrets.arn
}
