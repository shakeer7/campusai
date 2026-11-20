variable "environment" { type = string }
variable "s3_bucket_arn" { type = string }
variable "cluster_name" { type = string }
variable "oidc_provider_arn" {
  type    = string
  default = ""
}
variable "oidc_provider_url" {
  type    = string
  default = ""
}

# EKS Cluster Control Plane IAM Role
resource "aws_iam_role" "eks_cluster" {
  name = "campusai-${var.environment}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Managed Node Group IAM Role
resource "aws_iam_role" "eks_nodes" {
  name = "campusai-${var.environment}-eks-nodes-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "worker_node" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "cni" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "registry" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# Least-Privilege IAM Policy for AWS Bedrock Converse and S3 Documents Access
resource "aws_iam_policy" "bedrock_app_policy" {
  name        = "campusai-${var.environment}-bedrock-policy"
  description = "Allows CampusAI backend to invoke Bedrock Converse models and Titan embeddings"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:GetFoundationModelAvailability"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-*",
          "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:*",
          "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "polly:SynthesizeSpeech"
        ]
        Resource = "*"
      }
    ]
  })
}

# IRSA Role for CampusAI Backend ServiceAccount
resource "aws_iam_role" "bedrock_irsa" {
  name = "campusai-${var.environment}-backend-irsa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn != "" ? var.oidc_provider_arn : "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE"
      }
      Condition = {
        StringEquals = {
          "${replace(var.oidc_provider_url, "https://", "")}:sub" = "system:serviceaccount:campusai:campusai-backend-sa"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "bedrock_attach" {
  policy_arn = aws_iam_policy.bedrock_app_policy.arn
  role       = aws_iam_role.bedrock_irsa.name
}

output "eks_cluster_role_arn" { value = aws_iam_role.eks_cluster.arn }
output "eks_node_role_arn" { value = aws_iam_role.eks_nodes.arn }
output "bedrock_irsa_role_arn" { value = aws_iam_role.bedrock_irsa.arn }
