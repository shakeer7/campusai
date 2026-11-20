variable "aws_region" {
  type        = string
  description = "Target AWS region for deploying CampusAI infrastructure"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
  default     = "dev"
}

variable "use_aws_free_tier" {
  type        = bool
  description = "Optimize infrastructure for AWS Free Tier / Free Trial (t3.micro/t4g.micro, 20GB RDS, zero NAT cost)"
  default     = true
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones to span"
  default     = ["us-east-1a", "us-east-1b"]
}

variable "eks_cluster_name" {
  type        = string
  description = "Name of the Amazon EKS cluster"
  default     = "campusai-cluster"
}

variable "enable_eks_cluster" {
  type        = bool
  description = "Enable Amazon EKS cluster"
  default     = true
}

variable "eks_node_instance_types" {
  type        = list(string)
  description = "EC2 instance types for EKS nodes (m7 or c7 generation)"
  default     = ["m7i.large", "c7i.large"]
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance size (db.t4g.micro / db.t3.micro is AWS 750-hr/mo Free Tier eligible)"
  default     = "db.t4g.micro"
}

variable "db_name" {
  type        = string
  description = "Initial RDS database name"
  default     = "campusai_db"
}

variable "db_username" {
  type        = string
  description = "RDS Master username"
  default     = "campusai_admin"
}

variable "s3_bucket_name" {
  type        = string
  description = "S3 bucket for academic documents (5GB Free Tier eligible)"
  default     = "campusai-academic-cbit-528233125980"
}
