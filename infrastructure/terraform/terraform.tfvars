aws_region              = "us-east-1"
environment             = "dev"
enable_eks_cluster      = true
eks_cluster_name        = "campusai-cluster"
eks_node_instance_types = ["c7i-flex.large"]
use_aws_free_tier       = false
db_instance_class       = "db.t4g.micro"
s3_bucket_name          = "campusai-academic-cbit-528233125980"
