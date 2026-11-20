# ==============================================================================
# CampusAI: Automated Local AWS Infrastructure Provisioner (Free Tier)
# ==============================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 CampusAI: Local AWS Infrastructure Provisioning" -ForegroundColor Cyan
Write-Host "Mode: AWS Free Tier / Free Trial ($0.00 infrastructure bill)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verify Prerequisites
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Terraform is not installed or not in PATH. Please install Terraform (https://terraform.io)."
    exit 1
}

Write-Host "`n🔍 Verifying AWS CLI credentials..." -ForegroundColor Yellow
try {
    $caller = aws sts get-caller-identity | ConvertFrom-Json
    Write-Host "✅ Authenticated as: $($caller.Arn) (Account: $($caller.Account))" -ForegroundColor Green
} catch {
    Write-Warning "⚠️ Could not automatically verify AWS credentials via 'aws sts get-caller-identity'."
    Write-Host "Please ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set or configured via 'aws configure'."
    $proceed = Read-Host "Do you want to continue anyway? (y/n)"
    if ($proceed -ne "y") { exit 1 }
}

# 2. Change Directory to Terraform
$TerraformDir = Join-Path $PSScriptRoot "..\infrastructure\terraform"
Push-Location $TerraformDir

try {
    Write-Host "`n📦 Step 1: Initializing Terraform modules & plugins..." -ForegroundColor Yellow
    terraform init

    Write-Host "`n📋 Step 2: Generating Execution Plan (AWS Free Tier)..." -ForegroundColor Yellow
    terraform plan `
        -var="use_aws_free_tier=true" `
        -var="enable_eks_cluster=false" `
        -var="db_instance_class=db.t4g.micro" `
        -out="campusai_free_tier.tfplan"

    Write-Host "`n⚡ Step 3: Ready to provision AWS infrastructure." -ForegroundColor Yellow
    Write-Host "Resources to be created:"
    Write-Host "  - Custom VPC with Public/Private subnets (Zero NAT Gateway charges)"
    Write-Host "  - Amazon RDS PostgreSQL 16 with pgvector (db.t4g.micro - 750 hrs/mo Free Tier)"
    Write-Host "  - Amazon S3 Encrypted Academic Documents Bucket (5GB Free Tier)"
    Write-Host "  - Amazon ECR Repositories (backend, frontend, mcp) with lifecycle policy"
    Write-Host "  - IAM Roles for Bedrock Converse API access"
    Write-Host "  - AWS Secrets Manager secret for secure credentials"

    $confirm = Read-Host "`nApply this plan to your AWS account now? (y/n)"
    if ($confirm -eq "y") {
        Write-Host "`n🚀 Provisioning AWS Infrastructure..." -ForegroundColor Cyan
        terraform apply "campusai_free_tier.tfplan"

        Write-Host "`n============================================================" -ForegroundColor Green
        Write-Host "✅ AWS Infrastructure Successfully Provisioned!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green

        # Display outputs
        $rds = terraform output -raw rds_endpoint 2>$null
        $s3 = terraform output -raw s3_bucket_name 2>$null
        $ecr = terraform output -json ecr_repository_urls 2>$null

        Write-Host "`n📌 Next Steps: Deploy App Through GitHub" -ForegroundColor Cyan
        Write-Host "1. Add these Secrets to your GitHub Repository (Settings -> Secrets & Variables -> Actions):" -ForegroundColor White
        Write-Host "   - AWS_ACCESS_KEY_ID      : <Your AWS Access Key>" -ForegroundColor Yellow
        Write-Host "   - AWS_SECRET_ACCESS_KEY  : <Your AWS Secret Key>" -ForegroundColor Yellow
        Write-Host "   - AWS_REGION             : us-east-1" -ForegroundColor Yellow
        Write-Host "   - DATABASE_URL           : postgresql+psycopg://campusai_admin:<password>@$rds/campusai_db" -ForegroundColor Yellow
        Write-Host "`n2. Push your code to GitHub to trigger the automated deployment pipeline:" -ForegroundColor White
        Write-Host "   git remote add origin https://github.com/<your-username>/campusai.git" -ForegroundColor Green
        Write-Host "   git branch -M main" -ForegroundColor Green
        Write-Host "   git push -u origin main" -ForegroundColor Green
    } else {
        Write-Host "Provisioning skipped by user." -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}
