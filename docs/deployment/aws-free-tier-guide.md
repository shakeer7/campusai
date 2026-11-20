# CampusAI: AWS Free Tier & Free Trial Cost Optimization Guide

CampusAI has been engineered with a native **AWS Free Tier Profile** (`use_aws_free_tier = true`) allowing students, universities, and developers to deploy and evaluate the full production agentic college assistant without incurring cloud infrastructure bills.

---

## 1. AWS Free Tier Resource Allocation

| AWS Component | Standard Enterprise Cost | CampusAI Free Tier Configuration | Free Tier Allowance | Monthly Bill |
|:---|:---|:---|:---|:---|
| **Database (RDS)** | ~$90/month (db.t4g.medium) | `db.t4g.micro` (PostgreSQL 16 + pgvector) | 750 hours/month free (12 months) + 20 GB gp3 storage | **$0.00** |
| **Compute / Host** | ~$73/month (EKS Cluster fee) | EC2 `t3.micro` or `t2.micro` running Docker stack | 750 hours/month free (12 months) | **$0.00** |
| **Networking (NAT)** | ~$35/month + data egress | Public Subnet + Direct IGW Route | Free Internet Gateway | **$0.00** |
| **Document Storage (S3)** | ~$5/month | Standard Encrypted S3 Bucket | 5 GB free storage + 20,000 GET / 2,000 PUT requests | **$0.00** |
| **LLM Inference** | Variable per token | AWS Bedrock On-Demand or Local Mock Fallback | Pay-as-you-go (pennies) or `AWS_BEDROCK_MOCK_FALLBACK=true` | **$0.00** |

---

## 2. Deploying on AWS Free Tier

### Step 1: Clone and Configure Environment

```bash
git clone https://github.com/cbit-org/campusai.git
cd campusai
cp .env.example .env
```

Ensure the following flags are set in `.env`:
```ini
AWS_BEDROCK_MOCK_FALLBACK=true     # Zero model costs, deterministic high-fidelity responses
ENVIRONMENT=dev
```

### Step 2: Deploy Free Tier Infrastructure with Terraform

```bash
cd infrastructure/terraform

# Initialize Terraform modules without remote state locking
terraform init -backend=false

# Apply Free Tier configuration (db.t4g.micro, 20GB storage, no NAT Gateway charge)
terraform apply -var="use_aws_free_tier=true" -var="enable_eks_cluster=false"
```

### Step 3: Run CampusAI on Free Tier EC2 (`t3.micro`)

Launch an Amazon Linux 2023 or Ubuntu 24.04 `t3.micro` instance in the public subnet created by Terraform:

```bash
# On the EC2 instance:
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start CampusAI Stack
git clone https://github.com/cbit-org/campusai.git
cd campusai
docker-compose up -d
```

### Step 4: Verify Deployment and Seed Demo Data

```bash
# Execute synthetic CBIT college seeder
docker-compose exec backend python database/seed/seed_data.py
```

Verify services:
- Frontend UI: `http://<EC2-PUBLIC-IP>:3000`
- FastAPI Swagger Docs: `http://<EC2-PUBLIC-IP>:8000/docs`
- MCP Server Health: `http://<EC2-PUBLIC-IP>:8001/health`
- Prometheus Metrics: `http://<EC2-PUBLIC-IP>:9090`

---

## 3. Destroying Cloud Resources (Clean-up)

When you are done testing, run:

```bash
cd infrastructure/terraform
terraform destroy -var="use_aws_free_tier=true" -var="enable_eks_cluster=false"
```
All AWS resources will be cleanly removed, leaving zero residual charges.
