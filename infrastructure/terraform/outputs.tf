output "vpc_id" {
  description = "ID of the created VPC"
  value       = module.vpc.vpc_id
}

output "rds_endpoint" {
  description = "PostgreSQL RDS connection endpoint (Free Tier eligible db.t4g.micro/db.t3.micro)"
  value       = module.rds_pgvector.endpoint
}

output "s3_bucket_name" {
  description = "Academic documents S3 bucket name (5GB Free Tier eligible)"
  value       = module.s3.bucket_name
}

output "bedrock_app_role_arn" {
  description = "IAM Role ARN for Bedrock Converse model access"
  value       = module.iam.bedrock_irsa_role_arn
}

output "ecr_repository_urls" {
  description = "Amazon ECR Repository URLs for GitHub Actions pushes"
  value       = module.ecr.repository_urls
}

output "free_tier_mode" {
  description = "Whether AWS Free Tier cost-saving optimizations are enabled"
  value       = var.use_aws_free_tier
}

output "eks_cluster_name" {
  description = "Name of the EKS Cluster"
  value       = var.enable_eks_cluster ? module.eks[0].cluster_name : null
}

output "eks_cluster_endpoint" {
  description = "Endpoint for EKS Kubernetes API server"
  value       = var.enable_eks_cluster ? module.eks[0].cluster_endpoint : null
}
