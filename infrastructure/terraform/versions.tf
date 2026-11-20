terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }

  # Production S3 backend with DynamoDB state locking
  # backend "s3" {
  #   bucket         = "campusai-terraform-state-prod"
  #   key            = "environments/prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "campusai-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "CampusAI"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Compliance  = "CBIT-Academic-Cloud"
    }
  }
}
