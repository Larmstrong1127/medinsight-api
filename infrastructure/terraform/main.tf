terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment for team use — store state remotely
  # backend "s3" {
  #   bucket         = "medinsight-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region
}

# ── Networking ───────────────────────────────────────────────────────────────
module "networking" {
  source      = "./modules/networking"
  project     = var.project
  environment = var.environment
}

# ── Security (KMS, IAM) ──────────────────────────────────────────────────────
module "security" {
  source      = "./modules/security"
  project     = var.project
  environment = var.environment
  aws_region  = var.aws_region
  account_id  = data.aws_caller_identity.current.account_id
}

# ── Storage (S3, DynamoDB) ───────────────────────────────────────────────────
module "storage" {
  source      = "./modules/storage"
  project     = var.project
  environment = var.environment
  kms_key_arn = module.security.kms_key_arn
}

# ── ECS (Fargate) ────────────────────────────────────────────────────────────
module "ecs" {
  source              = "./modules/ecs"
  project             = var.project
  environment         = var.environment
  aws_region          = var.aws_region
  vpc_id              = module.networking.vpc_id
  private_subnet_ids  = module.networking.private_subnet_ids
  public_subnet_ids   = module.networking.public_subnet_ids
  task_execution_role = module.security.ecs_task_execution_role_arn
  task_role           = module.security.ecs_task_role_arn
  ecr_repository_url  = aws_ecr_repository.api.repository_url
  s3_bucket           = module.storage.documents_bucket
  dynamodb_table      = module.storage.documents_table
  audit_table         = module.storage.audit_table
  container_port      = 8000
  desired_count       = var.desired_count
}

# ── ECR ──────────────────────────────────────────────────────────────────────
resource "aws_ecr_repository" "api" {
  name                 = "${var.project}-api"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = module.security.kms_key_arn
  }

  tags = local.tags
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# ── CloudTrail (audit) ───────────────────────────────────────────────────────
resource "aws_cloudtrail" "main" {
  name                          = "${var.project}-trail"
  s3_bucket_name                = module.storage.cloudtrail_bucket
  include_global_service_events = true
  is_multi_region_trail         = false
  enable_log_file_validation    = true
  kms_key_id                    = module.security.kms_key_arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::${module.storage.documents_bucket}/"]
    }
  }

  tags = local.tags
}

data "aws_caller_identity" "current" {}

locals {
  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
