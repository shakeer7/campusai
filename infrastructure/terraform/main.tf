# Master Terraform Entrypoint for CampusAI Infrastructure
# Includes automated AWS Free Tier / Free Trial cost controls

module "vpc" {
  source             = "./modules/vpc"
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  environment        = var.environment
  cluster_name       = var.eks_cluster_name
  use_aws_free_tier  = var.use_aws_free_tier
}

module "s3" {
  source      = "./modules/s3"
  bucket_name = var.s3_bucket_name
  environment = var.environment
}

module "secrets" {
  source      = "./modules/secrets"
  environment = var.environment
  db_name     = var.db_name
  db_username = var.db_username
}

module "rds_pgvector" {
  source                = "./modules/rds_pgvector"
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.vpc.eks_nodes_sg_id
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = module.secrets.db_master_password
  instance_class        = var.db_instance_class
  use_aws_free_tier     = var.use_aws_free_tier
}

module "iam" {
  source             = "./modules/iam"
  environment        = var.environment
  s3_bucket_arn      = module.s3.bucket_arn
  cluster_name       = var.eks_cluster_name
}

# EKS Cluster is conditionally provisioned (disabled by default in Free Tier to save $73/mo cluster fee)
module "eks" {
  count                = var.enable_eks_cluster ? 1 : 0
  source               = "./modules/eks"
  cluster_name         = var.eks_cluster_name
  environment          = var.environment
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnet_ids
  node_instance_types  = var.eks_node_instance_types
  cluster_role_arn     = module.iam.eks_cluster_role_arn
  node_role_arn        = module.iam.eks_node_role_arn
}
