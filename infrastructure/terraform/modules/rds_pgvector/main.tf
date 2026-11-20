variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "app_security_group_id" { type = string }
variable "db_name" { type = string }
variable "db_username" { type = string }
variable "db_password" {
  type      = string
  sensitive = true
}
variable "instance_class" {
  type    = string
  default = "db.t4g.micro" # AWS Free Tier eligible
}
variable "use_aws_free_tier" {
  type    = bool
  default = true
}

resource "aws_db_subnet_group" "rds_subnets" {
  name        = "campusai-${var.environment}-rds-subnet-group"
  subnet_ids  = var.private_subnet_ids
  description = "Subnets for CampusAI RDS PostgreSQL"
}

resource "aws_security_group" "rds_sg" {
  name        = "campusai-${var.environment}-rds-sg"
  description = "Allows PostgreSQL traffic from application nodes"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "campusai-${var.environment}-rds-sg" }
}

# Parameter group supporting pgvector
resource "aws_db_parameter_group" "pgvector_pg" {
  name   = "campusai-${var.environment}-pgvector-pg"
  family = "postgres16"

  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }

  lifecycle { create_before_destroy = true }
}

resource "aws_db_instance" "postgres" {
  identifier             = "campusai-${var.environment}-db"
  engine                 = "postgres"
  engine_version         = "16.3"
  instance_class         = var.instance_class
  # 20GB storage is 100% Free Tier covered (AWS grants 20GB free storage/month)
  allocated_storage      = 20
  max_allocated_storage  = var.use_aws_free_tier ? 20 : 100
  storage_type           = "gp3"
  storage_encrypted      = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.rds_subnets.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  parameter_group_name   = aws_db_parameter_group.pgvector_pg.name

  multi_az               = false # Single-AZ for Free Tier compliance
  publicly_accessible    = false
  skip_final_snapshot    = true

  tags = {
    Name        = "campusai-${var.environment}-postgres"
    Tier        = var.use_aws_free_tier ? "AWS-Free-Tier" : "Standard"
  }
}

output "endpoint" { value = aws_db_instance.postgres.endpoint }
output "address" { value = aws_db_instance.postgres.address }
output "port" { value = aws_db_instance.postgres.port }
