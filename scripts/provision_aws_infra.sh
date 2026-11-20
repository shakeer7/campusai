#!/usr/bin/env bash
# ==============================================================================
# CampusAI: Automated Local AWS Infrastructure Provisioner (Free Tier)
# ==============================================================================
set -e

echo "============================================================"
echo "🚀 CampusAI: Local AWS Infrastructure Provisioning"
echo "Mode: AWS Free Tier / Free Trial ($0.00 infrastructure bill)"
echo "============================================================"

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install Terraform (https://terraform.io)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../infrastructure/terraform"

cd "$TERRAFORM_DIR"

echo "📦 Initializing Terraform modules..."
terraform init

echo "📋 Generating Execution Plan (AWS Free Tier)..."
terraform plan \
    -var="use_aws_free_tier=true" \
    -var="enable_eks_cluster=false" \
    -var="db_instance_class=db.t4g.micro" \
    -out="campusai_free_tier.tfplan"

read -p "Apply this plan to your AWS account now? (y/n): " confirm
if [ "$confirm" = "y" ]; then
    terraform apply "campusai_free_tier.tfplan"
    echo "✅ AWS Infrastructure Successfully Provisioned!"
    echo "Push code to GitHub to trigger the automated deployment pipeline."
else
    echo "Provisioning skipped."
fi
