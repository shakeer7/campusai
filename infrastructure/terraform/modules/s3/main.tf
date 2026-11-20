variable "bucket_name" { type = string }
variable "environment" { type = string }

resource "aws_s3_bucket" "academic_docs" {
  bucket        = var.bucket_name
  force_destroy = false

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
  }
}

# Server-Side Encryption using AES256 / AWS KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "s3_encrypt" {
  bucket = aws_s3_bucket.academic_docs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access for student confidentiality
resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket = aws_s3_bucket.academic_docs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.academic_docs.id
  versioning_configuration {
    status = "Enabled"
  }
}

output "bucket_name" { value = aws_s3_bucket.academic_docs.id }
output "bucket_arn" { value = aws_s3_bucket.academic_docs.arn }
